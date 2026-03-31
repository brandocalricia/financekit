import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from './useAuth';

export type SubscriptionStatus = 'free' | 'premium' | 'canceled';

interface SubscriptionData {
  status: SubscriptionStatus;
  stripe_customer_id: string | null;
  stripe_payment_intent_id: string | null;
  payment_method_last4: string | null;
  amount_paid: number;
  upgraded_at: string | null;
  created_at: string;
}

interface PaymentTransaction {
  id: string;
  stripe_payment_intent_id: string;
  amount: number;
  currency: string;
  status: string;
  payment_method_last4: string | null;
  created_at: string;
}

interface SubscriptionContextType {
  subscription: SubscriptionData | null;
  isPremium: boolean;
  loading: boolean;
  transactions: PaymentTransaction[];
  refresh: () => Promise<void>;
}

const SubscriptionContext = createContext<SubscriptionContextType | null>(null);

const FREE_DEFAULT: SubscriptionData = {
  status: 'free',
  stripe_customer_id: null,
  stripe_payment_intent_id: null,
  payment_method_last4: null,
  amount_paid: 0,
  upgraded_at: null,
  created_at: new Date().toISOString(),
};

export function SubscriptionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSubscription = useCallback(async () => {
    if (!user) {
      setSubscription(null);
      setTransactions([]);
      setLoading(false);
      return;
    }

    const [subRes, txRes] = await Promise.all([
      supabase
        .from('user_subscriptions')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle(),
      supabase
        .from('payment_transactions')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false }),
    ]);

    if (subRes.data) {
      setSubscription(subRes.data as SubscriptionData);
    } else {
      setSubscription(FREE_DEFAULT);
    }

    setTransactions((txRes.data || []) as PaymentTransaction[]);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  const isPremium = subscription?.status === 'premium';

  return (
    <SubscriptionContext.Provider value={{ subscription, isPremium, loading, transactions, refresh: fetchSubscription }}>
      {children}
    </SubscriptionContext.Provider>
  );
}

export function useSubscription() {
  const ctx = useContext(SubscriptionContext);
  if (!ctx) throw new Error('useSubscription must be used within SubscriptionProvider');
  return ctx;
}
