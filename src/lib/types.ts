export interface Transaction {
  id: string;
  user_id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  type: 'income' | 'expense';
  created_at: string;
}

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline: string | null;
  created_at: string;
}

export interface Holding {
  id: string;
  user_id: string;
  ticker: string;
  name: string;
  asset_type: 'stock' | 'crypto' | 'bond' | 'etf';
  quantity: number;
  avg_price: number;
  created_at: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  name: string;
  amount: number;
  frequency: 'monthly' | 'yearly' | 'weekly';
  category: string;
  active: boolean;
  created_at: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  display_name: string;
  currency: string;
  date_format: string;
  theme: 'light' | 'dark';
  accent_color: string;
}

export const ACCENT_PRESETS = [
  { name: 'Teal', value: '#2dd4bf' },
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Emerald', value: '#10b981' },
  { name: 'Rose', value: '#f43f5e' },
  { name: 'Amber', value: '#f59e0b' },
  { name: 'Sky', value: '#0ea5e9' },
  { name: 'Lime', value: '#84cc16' },
  { name: 'Orange', value: '#f97316' },
];

export const CATEGORIES = [
  'Food & Groceries',
  'Dining Out',
  'Transportation',
  'Housing',
  'Utilities',
  'Entertainment',
  'Shopping',
  'Healthcare',
  'Education',
  'Personal Care',
  'Savings',
  'Other',
];

export const SUBSCRIPTION_CATEGORIES = [
  'Streaming',
  'Music',
  'Software',
  'Gaming',
  'News',
  'Fitness',
  'Cloud Storage',
  'Other',
];

export const CURRENCIES: Record<string, string> = {
  USD: '$',
  EUR: '\u20AC',
  GBP: '\u00A3',
  CAD: 'C$',
  AUD: 'A$',
  JPY: '\u00A5',
  INR: '\u20B9',
  BRL: 'R$',
};
