import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { useSubscription } from '../hooks/useSubscription';
import { formatCurrency } from '../lib/format';
import { Plus, Trash2, TrendingUp } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import UpgradeBanner from '../components/UpgradeBanner';
import { DEMO_HOLDINGS, FREE_LIMITS } from '../lib/demoData';
import type { Holding } from '../lib/types';

export default function Portfolio() {
  const { user } = useAuth();
  const { settings } = useSettings();
  const { isPremium } = useSubscription();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);

  const [ticker, setTicker] = useState('');
  const [holdingName, setHoldingName] = useState('');
  const [assetType, setAssetType] = useState<Holding['asset_type']>('stock');
  const [quantity, setQuantity] = useState('');
  const [avgPrice, setAvgPrice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchHoldings = async () => {
    if (!user) return;
    if (!isPremium) {
      setHoldings(DEMO_HOLDINGS);
      setLoading(false);
      return;
    }
    const { data } = await supabase
      .from('holdings')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    setHoldings(data || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchHoldings();
  }, [user, isPremium]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !isPremium) return;
    setSubmitting(true);
    await supabase.from('holdings').insert({
      user_id: user.id,
      ticker: ticker.toUpperCase(),
      name: holdingName,
      asset_type: assetType,
      quantity: parseFloat(quantity),
      avg_price: parseFloat(avgPrice),
    });
    setTicker('');
    setHoldingName('');
    setQuantity('');
    setAvgPrice('');
    setSubmitting(false);
    fetchHoldings();
  };

  const handleDelete = async (id: string) => {
    if (!isPremium) return;
    await supabase.from('holdings').delete().eq('id', id);
    setHoldings((prev) => prev.filter((h) => h.id !== id));
  };

  const totalValue = holdings.reduce((s, h) => s + h.quantity * h.avg_price, 0);
  const totalCost = holdings.reduce((s, h) => s + h.quantity * h.avg_price, 0);

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2 className="page-title">Portfolio Tracker</h2>
            <p className="page-subtitle">Manage your investments</p>
          </div>
          {!isPremium && <DemoBadge />}
        </div>
      </div>

      {!isPremium && (
        <UpgradeBanner
          message={`You're viewing ${FREE_LIMITS.holdings} sample holdings. Upgrade to track your full portfolio.`}
        />
      )}

      <div className="stat-grid stat-grid--2">
        <div className="stat-card">
          <div className="stat-card-label">Portfolio Value</div>
          <div className="stat-card-value">{formatCurrency(totalValue, settings.currency)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Total Cost Basis</div>
          <div className="stat-card-value">{formatCurrency(totalCost, settings.currency)}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Add Holding</h3>
        </div>
        <div className="card-body">
          {!isPremium ? (
            <UpgradeBanner message="Upgrade to Premium to track your real investments." compact />
          ) : (
            <form onSubmit={handleAdd} className="form-grid">
              <div className="form-group">
                <label>Ticker</label>
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  placeholder="e.g., AAPL"
                  required
                />
              </div>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={holdingName}
                  onChange={(e) => setHoldingName(e.target.value)}
                  placeholder="e.g., Apple Inc."
                  required
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select value={assetType} onChange={(e) => setAssetType(e.target.value as Holding['asset_type'])}>
                  <option value="stock">Stock</option>
                  <option value="crypto">Crypto</option>
                  <option value="etf">ETF</option>
                  <option value="bond">Bond</option>
                </select>
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  step="any"
                  min="0.0001"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="10"
                  required
                />
              </div>
              <div className="form-group">
                <label>Avg. Price</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={avgPrice}
                  onChange={(e) => setAvgPrice(e.target.value)}
                  placeholder="150.00"
                  required
                />
              </div>
              <div className="form-group form-group--action">
                <button type="submit" className="btn btn--primary" disabled={submitting}>
                  <Plus size={16} />
                  {submitting ? 'Adding...' : 'Add Holding'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Holdings</h3>
        </div>
        <div className="card-body">
          {holdings.length === 0 ? (
            <div className="empty-state">
              <TrendingUp size={48} className="empty-state-icon" />
              <h3>No holdings yet</h3>
              <p className="empty-state-hint">Add your first stock or crypto above</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th className="text-right">Quantity</th>
                    <th className="text-right">Avg. Price</th>
                    <th className="text-right">Value</th>
                    {isPremium && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((h) => (
                    <tr key={h.id}>
                      <td className="text-bold">{h.ticker}</td>
                      <td>{h.name}</td>
                      <td><span className="badge">{h.asset_type}</span></td>
                      <td className="text-right">{h.quantity}</td>
                      <td className="text-right">{formatCurrency(h.avg_price, settings.currency)}</td>
                      <td className="text-right text-bold">
                        {formatCurrency(h.quantity * h.avg_price, settings.currency)}
                      </td>
                      {isPremium && (
                        <td>
                          <button
                            className="btn btn--icon btn--danger"
                            onClick={() => handleDelete(h.id)}
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
