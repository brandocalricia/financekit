function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  return [
    parseInt(h.substring(0, 2), 16),
    parseInt(h.substring(2, 4), 16),
    parseInt(h.substring(4, 6), 16),
  ];
}

function darken([r, g, b]: [number, number, number], amount: number): string {
  const f = 1 - amount;
  return `rgb(${Math.round(r * f)}, ${Math.round(g * f)}, ${Math.round(b * f)})`;
}

export function applyAccentColor(hex: string) {
  const rgb = hexToRgb(hex);
  const [r, g, b] = rgb;
  const root = document.documentElement;
  root.style.setProperty('--accent', hex);
  root.style.setProperty('--accent-hover', darken(rgb, 0.15));
  root.style.setProperty('--accent-muted', darken(rgb, 0.35));
  root.style.setProperty('--accent-glow', `rgba(${r}, ${g}, ${b}, 0.12)`);
  root.style.setProperty('--accent-glow-strong', `rgba(${r}, ${g}, ${b}, 0.2)`);
  root.style.setProperty('--border-focus', hex);
  root.style.setProperty('--shadow-glow', `0 0 20px rgba(${r}, ${g}, ${b}, 0.1)`);
}

export function applyTheme(theme: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', theme);
}
