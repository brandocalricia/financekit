import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { formatCurrency } from '../lib/format';
import { Plus, Trash2, Target, DollarSign } from 'lucide-react';
import type { Goal } from '../lib/types';

export default function Goals() {
  const { user } = useAuth();
  const { settings } = useSettings();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);

  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [current, setCurrent] = useState('');
  const [deadline, setDeadline] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [updateAmounts, setUpdateAmounts] = useState<Record<string, string>>({});

  const fetchGoals = async () => {
    if (!user) return;
    const { data } = await supabase
      .from('goals')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    setGoals(data || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchGoals();
  }, [user]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !target) return;
    setSubmitting(true);
    await supabase.from('goals').insert({
      user_id: user.id,
      name,
      target_amount: parseFloat(target),
      current_amount: current ? parseFloat(current) : 0,
      deadline: deadline || null,
    });
    setName('');
    setTarget('');
    setCurrent('');
    setDeadline('');
    setSubmitting(false);
    fetchGoals();
  };

  const handleUpdate = async (goalId: string) => {
    const addAmount = parseFloat(updateAmounts[goalId] || '0');
    if (!addAmount || addAmount <= 0) return;
    const goal = goals.find((g) => g.id === goalId);
    if (!goal) return;
    const newAmount = goal.current_amount + addAmount;
    await supabase
      .from('goals')
      .update({ current_amount: newAmount })
      .eq('id', goalId);
    setUpdateAmounts((prev) => ({ ...prev, [goalId]: '' }));
    fetchGoals();
  };

  const quickAdd = async (goalId: string, amount: number) => {
    const goal = goals.find((g) => g.id === goalId);
    if (!goal) return;
    await supabase
      .from('goals')
      .update({ current_amount: goal.current_amount + amount })
      .eq('id', goalId);
    fetchGoals();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this goal?')) return;
    await supabase.from('goals').delete().eq('id', id);
    setGoals((prev) => prev.filter((g) => g.id !== id));
  };

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Goal Tracker</h2>
        <p className="page-subtitle">Track your savings goals and milestones</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Create New Goal</h3>
        </div>
        <div className="card-body">
          <form onSubmit={handleAdd} className="form-grid">
            <div className="form-group">
              <label>Goal Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Emergency Fund"
                required
              />
            </div>
            <div className="form-group">
              <label>Target Amount</label>
              <input
                type="number"
                step="0.01"
                min="1"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="10000"
                required
              />
            </div>
            <div className="form-group">
              <label>Already Saved</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="form-group">
              <label>Deadline (optional)</label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>
            <div className="form-group form-group--action">
              <button type="submit" className="btn btn--primary" disabled={submitting}>
                <Plus size={16} />
                {submitting ? 'Creating...' : 'Create Goal'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {goals.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <div className="empty-state">
              <Target size={48} className="empty-state-icon" />
              <h3>No savings goals yet</h3>
              <p className="empty-state-hint">Add your first goal above to start tracking your progress</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="goals-grid">
          {goals.map((g) => {
            const pct = g.target_amount > 0
              ? Math.min(100, (g.current_amount / g.target_amount) * 100)
              : 0;
            const isComplete = pct >= 100;
            return (
              <div key={g.id} className={`card goal-card ${isComplete ? 'goal-card--complete' : ''}`}>
                <div className="card-body">
                  <div className="goal-card-top">
                    <div>
                      <h3 className="goal-card-name">{g.name}</h3>
                      {g.deadline && (
                        <span className="goal-card-deadline">
                          Deadline: {new Date(g.deadline).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <button
                      className="btn btn--icon btn--danger"
                      onClick={() => handleDelete(g.id)}
                      title="Delete goal"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <div className="goal-progress-section">
                    <div className="goal-progress-ring-wrapper">
                      <svg viewBox="0 0 100 100" className="goal-progress-ring">
                        <circle
                          cx="50" cy="50" r="42"
                          fill="none"
                          stroke="rgba(255,255,255,0.08)"
                          strokeWidth="8"
                        />
                        <circle
                          cx="50" cy="50" r="42"
                          fill="none"
                          stroke={isComplete ? '#22c55e' : '#2dd4bf'}
                          strokeWidth="8"
                          strokeLinecap="round"
                          strokeDasharray={`${2 * Math.PI * 42}`}
                          strokeDashoffset={`${2 * Math.PI * 42 * (1 - pct / 100)}`}
                          transform="rotate(-90 50 50)"
                          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
                        />
                        <text x="50" y="50" textAnchor="middle" dominantBaseline="central" className="goal-ring-text">
                          {pct.toFixed(0)}%
                        </text>
                      </svg>
                    </div>
                    <div className="goal-amounts">
                      <div className="goal-amounts-current">
                        {formatCurrency(g.current_amount, settings.currency)}
                      </div>
                      <div className="goal-amounts-target">
                        of {formatCurrency(g.target_amount, settings.currency)}
                      </div>
                    </div>
                  </div>

                  {!isComplete && (
                    <>
                      <div className="goal-quick-adds">
                        {[50, 100, 250, 500].map((amt) => (
                          <button
                            key={amt}
                            className="btn btn--small btn--outline"
                            onClick={() => quickAdd(g.id, amt)}
                          >
                            +{formatCurrency(amt, settings.currency)}
                          </button>
                        ))}
                      </div>
                      <div className="goal-custom-add">
                        <input
                          type="number"
                          step="0.01"
                          min="0.01"
                          placeholder="Custom amount"
                          value={updateAmounts[g.id] || ''}
                          onChange={(e) =>
                            setUpdateAmounts((prev) => ({ ...prev, [g.id]: e.target.value }))
                          }
                        />
                        <button
                          className="btn btn--primary btn--small"
                          onClick={() => handleUpdate(g.id)}
                        >
                          <DollarSign size={14} />
                          Add Funds
                        </button>
                      </div>
                    </>
                  )}

                  {isComplete && (
                    <div className="goal-complete-badge">Goal Reached!</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
