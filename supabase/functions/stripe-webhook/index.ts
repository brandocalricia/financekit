import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import Stripe from "npm:stripe@17.7.0";
import { createClient } from "npm:@supabase/supabase-js@2.49.4";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, X-Client-Info, Apikey",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET");

    if (!stripeKey || !webhookSecret) {
      return new Response(
        JSON.stringify({ error: "Stripe not configured" }),
        { status: 503, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const signature = req.headers.get("stripe-signature");
    if (!signature) {
      return new Response(
        JSON.stringify({ error: "Missing stripe signature" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const body = await req.text();
    const stripe = new Stripe(stripeKey);

    let event: Stripe.Event;
    try {
      event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret);
    } catch {
      return new Response(
        JSON.stringify({ error: "Invalid signature" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;
      const userId = session.metadata?.user_id;
      if (!userId) {
        return new Response(
          JSON.stringify({ error: "Missing user_id in metadata" }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
        );
      }

      const paymentIntentId =
        typeof session.payment_intent === "string"
          ? session.payment_intent
          : session.payment_intent?.id || session.id;

      const idempotencyKey = `checkout_${session.id}`;

      const { data: existingTx } = await supabase
        .from("payment_transactions")
        .select("id")
        .eq("idempotency_key", idempotencyKey)
        .maybeSingle();

      if (existingTx) {
        return new Response(
          JSON.stringify({ received: true, duplicate: true }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } },
        );
      }

      let last4: string | null = null;
      if (session.payment_intent && typeof session.payment_intent === "string") {
        try {
          const pi = await stripe.paymentIntents.retrieve(session.payment_intent);
          if (pi.payment_method && typeof pi.payment_method === "string") {
            const pm = await stripe.paymentMethods.retrieve(pi.payment_method);
            last4 = pm.card?.last4 || null;
          }
        } catch {
          // non-critical
        }
      }

      await supabase.from("payment_transactions").insert({
        user_id: userId,
        stripe_payment_intent_id: paymentIntentId,
        stripe_customer_id: typeof session.customer === "string" ? session.customer : null,
        amount: session.amount_total || 799,
        currency: session.currency || "usd",
        status: "succeeded",
        payment_method_last4: last4,
        idempotency_key: idempotencyKey,
      });

      await supabase
        .from("user_subscriptions")
        .upsert(
          {
            user_id: userId,
            status: "premium",
            stripe_customer_id:
              typeof session.customer === "string" ? session.customer : null,
            stripe_payment_intent_id: paymentIntentId,
            payment_method_last4: last4,
            amount_paid: session.amount_total || 799,
            upgraded_at: new Date().toISOString(),
          },
          { onConflict: "user_id" },
        );
    }

    if (event.type === "charge.refunded") {
      const charge = event.data.object as Stripe.Charge;
      const paymentIntentId =
        typeof charge.payment_intent === "string"
          ? charge.payment_intent
          : charge.payment_intent?.id;

      if (paymentIntentId) {
        const { data: tx } = await supabase
          .from("payment_transactions")
          .select("user_id")
          .eq("stripe_payment_intent_id", paymentIntentId)
          .maybeSingle();

        if (tx) {
          await supabase
            .from("payment_transactions")
            .update({ status: "refunded" })
            .eq("stripe_payment_intent_id", paymentIntentId);

          await supabase
            .from("user_subscriptions")
            .update({ status: "canceled" })
            .eq("user_id", tx.user_id);
        }
      }
    }

    return new Response(
      JSON.stringify({ received: true }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal server error";
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
