import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from './useAuth';
import { applyAccentColor, applyTheme } from '../lib/theme';

interface Settings {
  display_name: string;
  currency: string;
  date_format: string;
  theme: 'light' | 'dark';
  accent_color: string;
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (s: Partial<Settings>) => Promise<void>;
  loading: boolean;
}

const defaults: Settings = {
  display_name: '',
  currency: 'USD',
  date_format: 'MM/DD/YYYY',
  theme: 'dark',
  accent_color: '#2dd4bf',
};

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [settings, setSettings] = useState<Settings>(defaults);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    applyTheme(settings.theme);
  }, [settings.theme]);

  useEffect(() => {
    applyAccentColor(settings.accent_color);
  }, [settings.accent_color]);

  useEffect(() => {
    if (!user) {
      setSettings(defaults);
      applyTheme(defaults.theme);
      applyAccentColor(defaults.accent_color);
      setLoading(false);
      return;
    }
    (async () => {
      const { data } = await supabase
        .from('user_settings')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle();
      if (data) {
        const loaded: Settings = {
          display_name: data.display_name || '',
          currency: data.currency || 'USD',
          date_format: data.date_format || 'MM/DD/YYYY',
          theme: data.theme || 'dark',
          accent_color: data.accent_color || '#2dd4bf',
        };
        setSettings(loaded);
      }
      setLoading(false);
    })();
  }, [user]);

  const updateSettings = async (partial: Partial<Settings>) => {
    if (!user) return;
    const merged = { ...settings, ...partial };
    setSettings(merged);
    await supabase
      .from('user_settings')
      .upsert({
        user_id: user.id,
        ...merged,
      }, { onConflict: 'user_id' });
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, loading }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
}
