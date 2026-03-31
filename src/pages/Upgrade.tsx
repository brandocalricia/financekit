import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { Check, Wallet, Target, TrendingUp, RefreshCw, ChartBar as BarChart3, Shield, Zap, Crown } from 'lucide-react';

const FEATURES = [
  { label: 'Budget Tracker', free: 'Up to 5 transactions', premium: 'Unlimited', icon: Wallet },
  { label: 'Goal Tracker', free: 'Up to 2 goals', premium: 'Unlimited', icon: Target },
  { label: 'Portfolio Tracker', free: 'Up to 3 holdings', premium: 'Unlimited', icon: TrendingUp },
  { label: 'Subscription Auditor', free: 'Up to 3 subscriptions', premium: 'Unlimited', icon: RefreshCw },
  { label: 'Reports & Analytics', free: 'Basic overview', premium: 'Full analytics', icon: BarChart3 },
  { label: 'Data Storage', free: 'Sample data only', premium: 'Full cloud sync', icon: Shield },
];

export default function Upgrade() {
  const { user, session } = useAuth();
  const { isPremium, loading: subLoading } = useSubscription();
  const navigate = useNavigate();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState('');

  if (subLoading) return <div className="page-loading">Loading...</div>;

  if (isPremium) {
    return (
      <div className="page">
        <div className="upgrade-success-page">
          <div className="upgrade-success-icon">
            <Crown size={48} />
          </div>
          <h2>You're a Premium Member</h2>
          <p className="upgrade-success-text">
            You have full access to all FinanceKit features. Thank you for your support.
          </p>
          <button className="btn btn--primary" onClick={() => navigate('/')}>
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const handleCheckout = async () => {
    if (!user || !session) return;
    setCheckoutLoading(true);
    setError('');

    try {
      const apiUrl = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/stripe-checkout`;
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
          'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY,
        },
        body: JSON.stringify({
          return_url: window.location.origin,
        }),
      });

      const text = await res.text();
      let data: { url?: string; error?: string };
      try {
        data = JSON.parse(text);
      } catch {
        setError(`Server error (${res.status}): ${text.substring(0, 200)}`);
        setCheckoutLoading(false);
        return;
      }

      if (!res.ok) {
        setError(data.error || `Something went wrong (${res.status}).`);
        setCheckoutLoading(false);
        return;
      }

      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to payment service.');
      setCheckoutLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header" style={{ textAlign: 'center' }}>
        <h2 className="page-title">Upgrade to Premium</h2>
        <p className="page-subtitle">One-time payment. Lifetime access. No subscriptions.</p>
      </div>

      <div className="pricing-cards">
        <div className="pricing-card">
          <div className="pricing-card-header">
            <h3 className="pricing-card-title">Free</h3>
            <div className="pricing-card-price">$0</div>
            <p className="pricing-card-desc">Explore with sample data</p>
          </div>
          <ul className="pricing-features">
            {FEATURES.map(({ label, free }) => (
              <li key={label} className="pricing-feature">
                <Check size={16} className="pricing-feature-check pricing-feature-check--muted" />
                <span><strong>{label}:</strong> {free}</span>
              </li>
            ))}
          </ul>
          <div className="pricing-card-action">
            <span className="pricing-current-label">Current Plan</span>
          </div>
        </div>

        <div className="pricing-card pricing-card--premium">
          <div className="pricing-card-badge">Best Value</div>
          <div className="pricing-card-header">
            <h3 className="pricing-card-title">
              <Zap size={18} /> Premium
            </h3>
            <div className="pricing-card-price">
              $7<span className="pricing-card-cents">.99</span>
            </div>
            <p className="pricing-card-desc">One-time payment, forever yours</p>
          </div>
          <ul className="pricing-features">
            {FEATURES.map(({ label, premium }) => (
              <li key={label} className="pricing-feature">
                <Check size={16} className="pricing-feature-check" />
                <span><strong>{label}:</strong> {premium}</span>
              </li>
            ))}
          </ul>
          <div className="pricing-card-action">
            {error && <div className="alert alert--error">{error}</div>}
            <button
              className="btn btn--primary btn--full"
              onClick={handleCheckout}
              disabled={checkoutLoading}
            >
              {checkoutLoading ? 'Redirecting to Stripe...' : 'Get Premium for $7.99'}
            </button>
            <p className="pricing-card-note">
              Secure payment via Stripe. 30-day refund policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
