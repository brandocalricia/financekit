import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { formatCurrency } from '../lib/format';
import { TrendingDown, TrendingUp, ChartBar as BarChart3, RefreshCw, Target, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Transaction, Goal, Holding, Subscription } from '../lib/types';

export default function Dashboard() {
  const { user } = useAuth();
  const { settings } = useSettings();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    (async () => {
      const now = new Date();
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();

      const [txRes, goalRes, holdRes, subRes] = await Promise.all([
        supabase.from('transactions').select('*').eq('user_id', user.id).gte('date', monthStart).order('date', { ascending: false }),
        supabase.from('goals').select('*').eq('user_id', user.id),
        supabase.from('holdings').select('*').eq('user_id', user.id),
        supabase.from('subscriptions').select('*').eq('user_id', user.id).eq('active', true),
      ]);

      setTransactions(txRes.data || []);
      setGoals(goalRes.data || []);
      setHoldings(holdRes.data || []);
      setSubscriptions(subRes.data || []);
      setLoading(false);
    })();
  }, [user]);

  const monthlyExpenses = transactions
    .filter((t) => t.type === 'expense')
    .reduce((s, t) => s + t.amount, 0);

  const monthlyIncome = transactions
    .filter((t) => t.type === 'income')
    .reduce((s, t) => s + t.amount, 0);

  const portfolioValue = holdings.reduce((s, h) => s + h.quantity * h.avg_price, 0);

  const monthlySubs = subscriptions.reduce((s, sub) => {
    if (sub.frequency === 'yearly') return s + sub.amount / 12;
    if (sub.frequency === 'weekly') return s + sub.amount * 4.33;
    return s + sub.amount;
  }, 0);

  const categoryTotals = transactions
    .filter((t) => t.type === 'expense')
    .reduce<Record<string, number>>((acc, t) => {
      acc[t.category] = (acc[t.category] || 0) + t.amount;
      return acc;
    }, {});

  const sortedCategories = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1]);
  const maxCatAmount = sortedCategories.length > 0 ? sortedCategories[0][1] : 1;

  if (loading) {
    return <div className="page-loading">Loading dashboard...</div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Dashboard</h2>
        <p className="page-subtitle">Your financial overview this month</p>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Monthly Spending</span>
            <div className="stat-icon stat-icon--expense"><TrendingDown size={18} /></div>
          </div>
          <div className="stat-card-value stat-card-value--expense">
            {formatCurrency(monthlyExpenses, settings.currency)}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Monthly Income</span>
            <div className="stat-icon stat-icon--income"><TrendingUp size={18} /></div>
          </div>
          <div className="stat-card-value stat-card-value--income">
            {formatCurrency(monthlyIncome, settings.currency)}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Portfolio Value</span>
            <div className="stat-icon stat-icon--portfolio"><BarChart3 size={18} /></div>
          </div>
          <div className="stat-card-value">
            {formatCurrency(portfolioValue, settings.currency)}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Subscriptions / mo</span>
            <div className="stat-icon stat-icon--subs"><RefreshCw size={18} /></div>
          </div>
          <div className="stat-card-value stat-card-value--expense">
            {formatCurrency(monthlySubs, settings.currency)}
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3>Goals Progress</h3>
            <Link to="/goals" className="card-link">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="card-body">
            {goals.length === 0 ? (
              <div className="empty-state">
                <Target size={32} className="empty-state-icon" />
                <p>No savings goals yet</p>
                <Link to="/goals" className="btn btn--small btn--primary">Add your first goal</Link>
              </div>
            ) : (
              <div className="goals-list">
                {goals.slice(0, 4).map((g) => {
                  const pct = g.target_amount > 0
                    ? Math.min(100, (g.current_amount / g.target_amount) * 100)
                    : 0;
                  return (
                    <div key={g.id} className="goal-item">
                      <div className="goal-item-header">
                        <span className="goal-item-name">{g.name}</span>
                        <span className="goal-item-pct">{pct.toFixed(0)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className="progress-bar-fill"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: pct >= 100 ? 'var(--success)' : 'var(--accent)',
                          }}
                        />
                      </div>
                      <div className="goal-item-amounts">
                        <span>{formatCurrency(g.current_amount, settings.currency)}</span>
                        <span>{formatCurrency(g.target_amount, settings.currency)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Spending by Category</h3>
            <Link to="/budget" className="card-link">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="card-body">
            {sortedCategories.length === 0 ? (
              <div className="empty-state">
                <BarChart3 size={32} className="empty-state-icon" />
                <p>No transactions this month</p>
                <Link to="/budget" className="btn btn--small btn--primary">Add a transaction</Link>
              </div>
            ) : (
              <div className="category-list">
                {sortedCategories.slice(0, 6).map(([cat, amount]) => (
                  <div key={cat} className="category-item">
                    <div className="category-item-header">
                      <span className="category-item-name">{cat}</span>
                      <span className="category-item-amount">
                        {formatCurrency(amount, settings.currency)}
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${(amount / maxCatAmount) * 100}%` }}
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
          <h3>Recent Transactions</h3>
          <Link to="/budget" className="card-link">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="card-body">
          {transactions.length === 0 ? (
            <div className="empty-state">
              <p>No transactions this month</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th className="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.slice(0, 10).map((t) => (
                    <tr key={t.id}>
                      <td>{new Date(t.date).toLocaleDateString()}</td>
                      <td>{t.description}</td>
                      <td><span className="badge">{t.category}</span></td>
                      <td className={`text-right ${t.type === 'income' ? 'text-income' : 'text-expense'}`}>
                        {t.type === 'income' ? '+' : '-'}
                        {formatCurrency(t.amount, settings.currency)}
                      </td>
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
