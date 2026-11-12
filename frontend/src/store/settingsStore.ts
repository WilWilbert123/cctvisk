import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark' | 'system';

interface SettingsState {
  theme: ThemeMode;
  sidebarCollapsed: boolean;
  apiToken: string;
  setTheme: (theme: ThemeMode) => void;
  toggleSidebar: () => void;
  setApiToken: (token: string) => void;
}

function getInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  const saved = window.localStorage.getItem('cctv_theme') as ThemeMode | null;
  if (saved === 'light' || saved === 'dark' || saved === 'system') {
    return saved;
  }
  return 'light';
}

function getInitialToken(): string {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem('cctv_api_token') || '';
}

export function applyThemeToDocument(theme: ThemeMode) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const prefersDark = Boolean(
    typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-color-scheme: dark)')?.matches
  );

  const isDark = theme === 'dark' || (theme === 'system' && prefersDark);
  if (isDark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

export const useSettingsStore = create<SettingsState>((set) => ({
  theme: getInitialTheme(),
  sidebarCollapsed: false,
  apiToken: getInitialToken(),
  setTheme: (theme) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('cctv_theme', theme);
    }
    applyThemeToDocument(theme);
    set({ theme });
  },
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setApiToken: (token) => {
    if (typeof window !== 'undefined') {
      if (token) {
        window.localStorage.setItem('cctv_api_token', token);
      } else {
        window.localStorage.removeItem('cctv_api_token');
      }
    }
    set({ apiToken: token });
  },
}));
