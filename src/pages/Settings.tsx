import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { supabase } from '../lib/supabase';
import { CURRENCIES, ACCENT_PRESETS } from '../lib/types';
import { Save, Check, Sun, Moon, Palette } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const { settings, updateSettings } = useSettings();
  const [displayName, setDisplayName] = useState(settings.display_name);
  const [currency, setCurrency] = useState(settings.currency);
  const [dateFormat, setDateFormat] = useState(settings.date_format);
  const [saved, setSaved] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');

  const [customColor, setCustomColor] = useState(settings.accent_color);

  useEffect(() => {
    setDisplayName(settings.display_name);
    setCurrency(settings.currency);
    setDateFormat(settings.date_format);
    setCustomColor(settings.accent_color);
  }, [settings]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateSettings({
      display_name: displayName,
      currency,
      date_format: dateFormat,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError('');
    setPwSuccess('');

    if (newPassword.length < 8) {
      setPwError('Password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwError('Passwords do not match');
      return;
    }

    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    });

    if (error) {
      setPwError(error.message);
    } else {
      setPwSuccess('Password updated successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    }
  };

  const handleThemeChange = (theme: 'light' | 'dark') => {
    updateSettings({ theme });
  };

  const handleAccentPreset = (color: string) => {
    setCustomColor(color);
    updateSettings({ accent_color: color });
  };

  const handleCustomColorChange = (color: string) => {
    setCustomColor(color);
    updateSettings({ accent_color: color });
  };

  const isPreset = ACCENT_PRESETS.some((p) => p.value === settings.accent_color);

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Settings</h2>
        <p className="page-subtitle">Manage your account and appearance</p>
      </div>

      <div className="settings-grid">
        <div className="card">
          <div className="card-header">
            <h3>Profile</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleSaveProfile} className="form-stack">
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={user?.email || ''} disabled />
              </div>
              <div className="form-group">
                <label>Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Your name"
                />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  {Object.entries(CURRENCIES).map(([code, symbol]) => (
                    <option key={code} value={code}>{code} ({symbol})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Date Format</label>
                <select value={dateFormat} onChange={(e) => setDateFormat(e.target.value)}>
                  <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                  <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                </select>
              </div>
              <button type="submit" className="btn btn--primary">
                {saved ? <><Check size={16} /> Saved</> : <><Save size={16} /> Save Changes</>}
              </button>
            </form>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Appearance</h3>
          </div>
          <div className="card-body">
            <div className="form-stack">
              <div className="form-group">
                <label>Theme</label>
                <div className="theme-toggle-group">
                  <button
                    type="button"
                    className={`theme-toggle-option ${settings.theme === 'light' ? 'theme-toggle-option--active' : ''}`}
                    onClick={() => handleThemeChange('light')}
                  >
                    <Sun size={16} /> Light
                  </button>
                  <button
                    type="button"
                    className={`theme-toggle-option ${settings.theme === 'dark' ? 'theme-toggle-option--active' : ''}`}
                    onClick={() => handleThemeChange('dark')}
                  >
                    <Moon size={16} /> Dark
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label>Accent Color</label>
                <div className="accent-presets">
                  {ACCENT_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      className={`accent-swatch ${settings.accent_color === preset.value ? 'accent-swatch--active' : ''}`}
                      onClick={() => handleAccentPreset(preset.value)}
                      title={preset.name}
                    >
                      <span
                        className="accent-swatch-inner"
                        style={{ background: preset.value }}
                      >
                        {settings.accent_color === preset.value && (
                          <Check size={14} className="accent-swatch-check" />
                        )}
                      </span>
                    </button>
                  ))}
                </div>
                <div className="accent-custom-row">
                  <input
                    type="color"
                    className="accent-custom-input"
                    value={customColor}
                    onChange={(e) => handleCustomColorChange(e.target.value)}
                    title="Pick a custom color"
                  />
                  <div>
                    <span className="accent-custom-label">
                      {isPreset ? 'Or pick a custom color' : 'Custom color'}
                    </span>
                    {!isPreset && (
                      <span className="accent-custom-hex"> {settings.accent_color}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Change Password</h3>
          </div>
          <div className="card-body">
            {pwError && <div className="alert alert--error">{pwError}</div>}
            {pwSuccess && <div className="alert alert--success">{pwSuccess}</div>}
            <form onSubmit={handleChangePassword} className="form-stack">
              <div className="form-group">
                <label>Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </div>
              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  minLength={8}
                  required
                />
              </div>
              <div className="form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  required
                />
              </div>
              <button type="submit" className="btn btn--primary">
                <Save size={16} /> Update Password
              </button>
            </form>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>About</h3>
          </div>
          <div className="card-body">
            <div className="settings-about">
              <div className="settings-about-row">
                <span className="settings-about-label">Version</span>
                <span className="badge">9.2</span>
              </div>
              <div className="settings-about-row">
                <span className="settings-about-label">Theme</span>
                <span className="badge">{settings.theme === 'dark' ? 'Dark' : 'Light'}</span>
              </div>
              <div className="settings-about-row">
                <span className="settings-about-label">Accent</span>
                <span className="badge badge--accent" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Palette size={12} />
                  {ACCENT_PRESETS.find((p) => p.value === settings.accent_color)?.name || 'Custom'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
