import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { useSubscription } from '../hooks/useSubscription';
import { formatCurrency } from '../lib/format';
import { Plus, Trash2, Wallet } from 'lucide-react';
import { CATEGORIES } from '../lib/types';
import DemoBadge from '../components/DemoBadge';
import UpgradeBanner from '../components/UpgradeBanner';
import { DEMO_TRANSACTIONS, FREE_LIMITS } from '../lib/demoData';
import type { Transaction } from '../lib/types';

export default function Budget() {
  const { user } = useAuth();
  const { settings } = useSettings();
  const { isPremium } = useSubscription();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [type, setType] = useState<'expense' | 'income'>('expense');
  const [submitting, setSubmitting] = useState(false);

  const fetchTransactions = async () => {
    if (!user) return;
    if (!isPremium) {
      setTransactions(DEMO_TRANSACTIONS);
      setLoading(false);
      return;
    }
    const { data } = await supabase
      .from('transactions')
      .select('*')
      .eq('user_id', user.id)
      .order('date', { ascending: false });
    setTransactions(data || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchTransactions();
  }, [user, isPremium]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !amount || !isPremium) return;
    setSubmitting(true);
    await supabase.from('transactions').insert({
      user_id: user.id,
      date,
      description,
      amount: parseFloat(amount),
      category,
      type,
    });
    setDescription('');
    setAmount('');
    setSubmitting(false);
    fetchTransactions();
  };

  const handleDelete = async (id: string) => {
    if (!isPremium) return;
    await supabase.from('transactions').delete().eq('id', id);
    setTransactions((prev) => prev.filter((t) => t.id !== id));
  };

  const now = new Date();
  const monthTransactions = transactions.filter((t) => {
    const d = new Date(t.date);
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  });

  const totalSpent = monthTransactions
    .filter((t) => t.type === 'expense')
    .reduce((s, t) => s + t.amount, 0);

  const totalIncome = monthTransactions
    .filter((t) => t.type === 'income')
    .reduce((s, t) => s + t.amount, 0);

  const categoryTotals = monthTransactions
    .filter((t) => t.type === 'expense')
    .reduce<Record<string, number>>((acc, t) => {
      acc[t.category] = (acc[t.category] || 0) + t.amount;
      return acc;
    }, {});

  const sortedCategories = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1]);
  const maxCatAmount = sortedCategories.length > 0 ? sortedCategories[0][1] : 1;

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2 className="page-title">Budget Tracker</h2>
            <p className="page-subtitle">Track your income and expenses</p>
          </div>
          {!isPremium && <DemoBadge />}
        </div>
      </div>

      {!isPremium && (
        <UpgradeBanner
          message={`You're viewing ${FREE_LIMITS.transactions} sample transactions. Upgrade for unlimited tracking.`}
        />
      )}

      <div className="stat-grid stat-grid--3">
        <div className="stat-card">
          <div className="stat-card-label">Spent This Month</div>
          <div className="stat-card-value stat-card-value--expense">
            {formatCurrency(totalSpent, settings.currency)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Income This Month</div>
          <div className="stat-card-value stat-card-value--income">
            {formatCurrency(totalIncome, settings.currency)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Net This Month</div>
          <div className={`stat-card-value ${totalIncome - totalSpent >= 0 ? 'stat-card-value--income' : 'stat-card-value--expense'}`}>
            {formatCurrency(totalIncome - totalSpent, settings.currency)}
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3>Add Transaction</h3>
          </div>
          <div className="card-body">
            {!isPremium ? (
              <UpgradeBanner message="Upgrade to Premium to add your own transactions." compact />
            ) : (
              <form onSubmit={handleAdd} className="form-grid">
                <div className="form-group">
                  <label>Date</label>
                  <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g., Grocery store"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value)}>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Type</label>
                  <select value={type} onChange={(e) => setType(e.target.value as 'expense' | 'income')}>
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
                <div className="form-group form-group--action">
                  <button type="submit" className="btn btn--primary" disabled={submitting}>
                    <Plus size={16} />
                    {submitting ? 'Adding...' : 'Add'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Spending by Category</h3>
          </div>
          <div className="card-body">
            {sortedCategories.length === 0 ? (
              <div className="empty-state">
                <Wallet size={32} className="empty-state-icon" />
                <p>No expenses this month</p>
              </div>
            ) : (
              <div className="category-list">
                {sortedCategories.map(([cat, amt]) => (
                  <div key={cat} className="category-item">
                    <div className="category-item-header">
                      <span className="category-item-name">{cat}</span>
                      <span className="category-item-amount">
                        {formatCurrency(amt, settings.currency)}
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${(amt / maxCatAmount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>All Transactions</h3>
        </div>
        <div className="card-body">
          {transactions.length === 0 ? (
            <div className="empty-state">
              <Wallet size={32} className="empty-state-icon" />
              <p>No transactions yet</p>
              <p className="empty-state-hint">Add your first transaction using the form above</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th className="text-right">Amount</th>
                    {isPremium && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id}>
                      <td>{new Date(t.date).toLocaleDateString()}</td>
                      <td>{t.description}</td>
                      <td><span className="badge">{t.category}</span></td>
                      <td>
                        <span className={`badge ${t.type === 'income' ? 'badge--income' : 'badge--expense'}`}>
                          {t.type}
                        </span>
                      </td>
                      <td className={`text-right ${t.type === 'income' ? 'text-income' : 'text-expense'}`}>
                        {t.type === 'income' ? '+' : '-'}
                        {formatCurrency(t.amount, settings.currency)}
                      </td>
                      {isPremium && (
                        <td>
                          <button
                            className="btn btn--icon btn--danger"
                            onClick={() => handleDelete(t.id)}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
