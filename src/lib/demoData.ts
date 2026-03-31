import type { Transaction, Goal, Holding, Subscription } from './types';

const DEMO_ID = 'demo';

export const DEMO_TRANSACTIONS: Transaction[] = [
  {
    id: `${DEMO_ID}-tx-1`,
    user_id: DEMO_ID,
    date: new Date().toISOString().split('T')[0],
    description: 'Grocery Store',
    amount: 87.42,
    category: 'Food & Groceries',
    type: 'expense',
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-tx-2`,
    user_id: DEMO_ID,
    date: new Date().toISOString().split('T')[0],
    description: 'Monthly Salary',
    amount: 4500.00,
    category: 'Other',
    type: 'income',
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-tx-3`,
    user_id: DEMO_ID,
    date: new Date(Date.now() - 86400000 * 2).toISOString().split('T')[0],
    description: 'Electric Bill',
    amount: 124.30,
    category: 'Utilities',
    type: 'expense',
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-tx-4`,
    user_id: DEMO_ID,
    date: new Date(Date.now() - 86400000 * 3).toISOString().split('T')[0],
    description: 'Coffee Shop',
    amount: 5.75,
    category: 'Dining Out',
    type: 'expense',
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-tx-5`,
    user_id: DEMO_ID,
    date: new Date(Date.now() - 86400000 * 5).toISOString().split('T')[0],
    description: 'Freelance Payment',
    amount: 750.00,
    category: 'Other',
    type: 'income',
    created_at: new Date().toISOString(),
  },
];

export const DEMO_GOALS: Goal[] = [
  {
    id: `${DEMO_ID}-goal-1`,
    user_id: DEMO_ID,
    name: 'Emergency Fund',
    target_amount: 10000,
    current_amount: 6250,
    deadline: new Date(Date.now() + 86400000 * 180).toISOString().split('T')[0],
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-goal-2`,
    user_id: DEMO_ID,
    name: 'Vacation Savings',
    target_amount: 3000,
    current_amount: 1200,
    deadline: new Date(Date.now() + 86400000 * 90).toISOString().split('T')[0],
    created_at: new Date().toISOString(),
  },
];

export const DEMO_HOLDINGS: Holding[] = [
  {
    id: `${DEMO_ID}-hold-1`,
    user_id: DEMO_ID,
    ticker: 'AAPL',
    name: 'Apple Inc.',
    asset_type: 'stock',
    quantity: 15,
    avg_price: 178.50,
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-hold-2`,
    user_id: DEMO_ID,
    ticker: 'VOO',
    name: 'Vanguard S&P 500 ETF',
    asset_type: 'etf',
    quantity: 8,
    avg_price: 412.30,
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-hold-3`,
    user_id: DEMO_ID,
    ticker: 'BTC',
    name: 'Bitcoin',
    asset_type: 'crypto',
    quantity: 0.25,
    avg_price: 42000,
    created_at: new Date().toISOString(),
  },
];

export const DEMO_SUBSCRIPTIONS: Subscription[] = [
  {
    id: `${DEMO_ID}-sub-1`,
    user_id: DEMO_ID,
    name: 'Netflix',
    amount: 15.99,
    frequency: 'monthly',
    category: 'Streaming',
    active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-sub-2`,
    user_id: DEMO_ID,
    name: 'Spotify',
    amount: 10.99,
    frequency: 'monthly',
    category: 'Music',
    active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: `${DEMO_ID}-sub-3`,
    user_id: DEMO_ID,
    name: 'iCloud Storage',
    amount: 2.99,
    frequency: 'monthly',
    category: 'Cloud Storage',
    active: true,
    created_at: new Date().toISOString(),
  },
];

export const FREE_LIMITS = {
  transactions: 5,
  goals: 2,
  holdings: 3,
  subscriptions: 3,
};
