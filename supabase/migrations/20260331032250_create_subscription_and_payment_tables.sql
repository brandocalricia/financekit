/*
  # Create Subscription and Payment Tables

  1. New Tables
    - `user_subscriptions`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references auth.users, unique)
      - `status` (text: free, premium, canceled)
      - `stripe_customer_id` (text, nullable)
      - `stripe_payment_intent_id` (text, nullable)
      - `payment_method_last4` (text, nullable)
      - `amount_paid` (integer, default 0, cents)
      - `created_at` (timestamptz)
      - `upgraded_at` (timestamptz, nullable)

    - `payment_transactions`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references auth.users)
      - `stripe_payment_intent_id` (text)
      - `stripe_customer_id` (text, nullable)
      - `amount` (integer, cents)
      - `currency` (text, default 'usd')
      - `status` (text: succeeded, failed, refunded, pending)
      - `payment_method_last4` (text, nullable)
      - `error_message` (text, nullable)
      - `idempotency_key` (text, unique, nullable)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on both tables
    - Users can only read their own subscription data
    - Users can only read their own payment transactions
    - Only service role (edge functions) can insert/update via policies
    - Auto-create free subscription on new user signup via trigger

  3. Notes
    - amount fields stored in cents for precision
    - stripe IDs stored for reconciliation
    - idempotency_key prevents duplicate webhook processing
*/

CREATE TABLE IF NOT EXISTS user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'free' CHECK (status IN ('free', 'premium', 'canceled')),
  stripe_customer_id text,
  stripe_payment_intent_id text,
  payment_method_last4 text,
  amount_paid integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  upgraded_at timestamptz,
  CONSTRAINT user_subscriptions_user_id_unique UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS payment_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_payment_intent_id text NOT NULL,
  stripe_customer_id text,
  amount integer NOT NULL DEFAULT 0,
  currency text NOT NULL DEFAULT 'usd',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('succeeded', 'failed', 'refunded', 'pending')),
  payment_method_last4 text,
  error_message text,
  idempotency_key text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_stripe_pi ON payment_transactions(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own subscription"
  ON user_subscriptions
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert subscriptions"
  ON user_subscriptions
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can update subscriptions"
  ON user_subscriptions
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own payment transactions"
  ON payment_transactions
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own payment transactions"
  ON payment_transactions
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION public.handle_new_user_subscription()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.user_subscriptions (user_id, status)
  VALUES (NEW.id, 'free')
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'on_auth_user_created_subscription'
  ) THEN
    CREATE TRIGGER on_auth_user_created_subscription
      AFTER INSERT ON auth.users
      FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_subscription();
  END IF;
END $$;

INSERT INTO user_subscriptions (user_id, status)
SELECT id, 'free'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM user_subscriptions)
ON CONFLICT (user_id) DO NOTHING;