import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useSubscription } from '../hooks/useSubscription';
import { CircleCheck as CheckCircle, ArrowRight, Loader } from 'lucide-react';

export default function CheckoutSuccess() {
  const { isPremium, refresh } = useSubscription();
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    if (isPremium || attempts >= 10) return;

    const timer = setTimeout(() => {
      refresh();
      setAttempts((a) => a + 1);
    }, 2000);

    return () => clearTimeout(timer);
  }, [isPremium, attempts, refresh]);

  return (
    <div className="page">
      <div className="checkout-success">
        {isPremium ? (
          <>
            <div className="checkout-success-icon">
              <CheckCircle size={56} />
            </div>
            <h2>Payment Successful</h2>
            <p className="checkout-success-text">
              Thank you for upgrading to FinanceKit Premium.
              All features are now unlocked.
            </p>
            <Link to="/" className="btn btn--primary">
              Go to Dashboard <ArrowRight size={16} />
            </Link>
          </>
        ) : (
          <>
            <div className="checkout-success-icon checkout-success-icon--pending">
              <Loader size={56} className="spin-icon" />
            </div>
            <h2>Processing Payment</h2>
            <p className="checkout-success-text">
              Your payment is being confirmed. This usually takes just a few seconds.
            </p>
            {attempts >= 10 && (
              <p className="checkout-success-note">
                Taking longer than expected. Your payment was received and your account
                will be upgraded shortly. You can safely navigate away.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
