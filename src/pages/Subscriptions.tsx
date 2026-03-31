import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { useSubscription } from '../hooks/useSubscription';
import { formatCurrency } from '../lib/format';
import { Plus, Trash2, RefreshCw } from 'lucide-react';
import { SUBSCRIPTION_CATEGORIES } from '../lib/types';
import DemoBadge from '../components/DemoBadge';
import UpgradeBanner from '../components/UpgradeBanner';
import { DEMO_SUBSCRIPTIONS, FREE_LIMITS } from '../lib/demoData';
import type { Subscription } from '../lib/types';

export default function Subscriptions() {
  const { user } = useAuth();
  const { settings } = useSettings();
  const { isPremium } = useSubscription();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);

  const [name, setName] = useState('');
  const [amount, setAmount] = useState('');
  const [frequency, setFrequency] = useState<Subscription['frequency']>('monthly');
  const [category, setCategory] = useState(SUBSCRIPTION_CATEGORIES[0]);
  const [submitting, setSubmitting] = useState(false);

  const fetchSubs = async () => {
    if (!user) return;
    if (!isPremium) {
      setSubscriptions(DEMO_SUBSCRIPTIONS);
      setLoading(false);
      return;
    }
    const { data } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    setSubscriptions(data || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchSubs();
  }, [user, isPremium]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !isPremium) return;
    setSubmitting(true);
    await supabase.from('subscriptions').insert({
      user_id: user.id,
      name,
      amount: parseFloat(amount),
      frequency,
      category,
      active: true,
    });
    setName('');
    setAmount('');
    setSubmitting(false);
    fetchSubs();
  };

  const handleDelete = async (id: string) => {
    if (!isPremium) return;
    await supabase.from('subscriptions').delete().eq('id', id);
    setSubscriptions((prev) => prev.filter((s) => s.id !== id));
  };

  const toggleActive = async (sub: Subscription) => {
    if (!isPremium) return;
    await supabase
      .from('subscriptions')
      .update({ active: !sub.active })
      .eq('id', sub.id);
    fetchSubs();
  };

  const activeSubs = subscriptions.filter((s) => s.active);

  const monthlyCost = activeSubs.reduce((s, sub) => {
    if (sub.frequency === 'yearly') return s + sub.amount / 12;
    if (sub.frequency === 'weekly') return s + sub.amount * 4.33;
    return s + sub.amount;
  }, 0);

  const yearlyCost = monthlyCost * 12;

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2 className="page-title">Subscription Auditor</h2>
            <p className="page-subtitle">Track and manage your recurring subscriptions</p>
          </div>
          {!isPremium && <DemoBadge />}
        </div>
      </div>

      {!isPremium && (
        <UpgradeBanner
          message={`You're viewing ${FREE_LIMITS.subscriptions} sample subscriptions. Upgrade to track all of yours.`}
        />
      )}

      <div className="stat-grid stat-grid--3">
        <div className="stat-card">
          <div className="stat-card-label">Monthly Cost</div>
          <div className="stat-card-value stat-card-value--expense">
            {formatCurrency(monthlyCost, settings.currency)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Yearly Cost</div>
          <div className="stat-card-value stat-card-value--expense">
            {formatCurrency(yearlyCost, settings.currency)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Active Subscriptions</div>
          <div className="stat-card-value">{activeSubs.length}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Add Subscription</h3>
        </div>
        <div className="card-body">
          {!isPremium ? (
            <UpgradeBanner message="Upgrade to Premium to track your own subscriptions." compact />
          ) : (
            <form onSubmit={handleAdd} className="form-grid">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Netflix"
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
                  placeholder="15.99"
                  required
                />
              </div>
              <div className="form-group">
                <label>Frequency</label>
                <select value={frequency} onChange={(e) => setFrequency(e.target.value as Subscription['frequency'])}>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <div className="form-group">
                <label>Category</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  {SUBSCRIPTION_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
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
          <h3>Your Subscriptions</h3>
        </div>
        <div className="card-body">
          {subscriptions.length === 0 ? (
            <div className="empty-state">
              <RefreshCw size={48} className="empty-state-icon" />
              <h3>No subscriptions yet</h3>
              <p className="empty-state-hint">Add your recurring subscriptions to track monthly costs</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Frequency</th>
                    <th className="text-right">Amount</th>
                    <th className="text-right">Monthly Equiv.</th>
                    <th>Status</th>
                    {isPremium && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {subscriptions.map((s) => {
                    const monthlyEquiv =
                      s.frequency === 'yearly' ? s.amount / 12
                      : s.frequency === 'weekly' ? s.amount * 4.33
                      : s.amount;
                    return (
                      <tr key={s.id} className={!s.active ? 'row--inactive' : ''}>
                        <td className="text-bold">{s.name}</td>
                        <td><span className="badge">{s.category}</span></td>
                        <td>{s.frequency}</td>
                        <td className="text-right">{formatCurrency(s.amount, settings.currency)}</td>
                        <td className="text-right">{formatCurrency(monthlyEquiv, settings.currency)}</td>
                        <td>
                          <button
                            className={`badge badge--clickable ${s.active ? 'badge--income' : 'badge--expense'}`}
                            onClick={() => toggleActive(s)}
                            disabled={!isPremium}
                          >
                            {s.active ? 'Active' : 'Cancelled'}
                          </button>
                        </td>
                        {isPremium && (
                          <td>
                            <button
                              className="btn btn--icon btn--danger"
                              onClick={() => handleDelete(s.id)}
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
