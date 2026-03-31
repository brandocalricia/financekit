import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4" />
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853" />
      <path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332Z" fill="#FBBC05" />
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.166 6.656 3.58 9 3.58Z" fill="#EA4335" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
      <path d="M9 0C4.03 0 0 4.03 0 9c0 3.98 2.58 7.35 6.16 8.54.45.08.62-.2.62-.43 0-.21-.01-.77-.01-1.51-2.51.55-3.04-1.21-3.04-1.21-.41-1.04-1-1.32-1-1.32-.82-.56.06-.55.06-.55.9.06 1.38.93 1.38.93.8 1.37 2.1.98 2.62.75.08-.58.31-.98.57-1.2-2-.23-4.1-1-4.1-4.46 0-.98.35-1.79.93-2.42-.09-.23-.4-1.15.09-2.39 0 0 .76-.24 2.48.93a8.6 8.6 0 0 1 2.26-.3c.77 0 1.54.1 2.26.3 1.73-1.17 2.48-.93 2.48-.93.49 1.24.18 2.16.09 2.39.58.63.93 1.44.93 2.42 0 3.47-2.11 4.23-4.12 4.45.32.28.61.83.61 1.68 0 1.21-.01 2.19-.01 2.49 0 .24.16.52.62.43A9.01 9.01 0 0 0 18 9c0-4.97-4.03-9-9-9Z" />
    </svg>
  );
}

export default function OAuthButtons() {
  const { signInWithOAuth } = useAuth();
  const [oauthError, setOauthError] = useState('');

  const handleOAuth = async (provider: 'google' | 'github') => {
    setOauthError('');
    const { error } = await signInWithOAuth(provider);
    if (error) setOauthError(error);
  };

  return (
    <>
      {oauthError && <div className="alert alert--error">{oauthError}</div>}
      <div className="oauth-buttons">
        <button
          type="button"
          className="btn btn--oauth"
          onClick={() => handleOAuth('google')}
        >
          <GoogleIcon />
          <span>Google</span>
        </button>
        <button
          type="button"
          className="btn btn--oauth btn--oauth-github"
          onClick={() => handleOAuth('github')}
        >
          <GitHubIcon />
          <span>GitHub</span>
        </button>
      </div>
    </>
  );
}
