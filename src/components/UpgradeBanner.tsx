import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

interface UpgradeBannerProps {
  message: string;
  compact?: boolean;
}

export default function UpgradeBanner({ message, compact }: UpgradeBannerProps) {
  if (compact) {
    return (
      <div className="upgrade-banner upgrade-banner--compact">
        <Sparkles size={14} />
        <span>{message}</span>
        <Link to="/upgrade" className="upgrade-banner-link">Upgrade</Link>
      </div>
    );
  }

  return (
    <div className="upgrade-banner">
      <div className="upgrade-banner-content">
        <Sparkles size={16} />
        <span>{message}</span>
      </div>
      <Link to="/upgrade" className="btn btn--small btn--primary">
        Upgrade to Premium
      </Link>
    </div>
  );
}
