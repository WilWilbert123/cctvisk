import React, { useEffect } from 'react';
import { BrowserRouter, HashRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRoutes } from './routes';
import { createRealtimeSocket } from './services/api';
import { applyThemeToDocument, useSettingsStore } from './store/settingsStore';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 4000,
    },
  },
});

const RouterComponent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAndroidApk =
    typeof window !== 'undefined' &&
    (window.location.protocol === 'file:' || Boolean((window as any).AndroidNativeScanner));
  return isAndroidApk ? (
    <HashRouter>{children}</HashRouter>
  ) : (
    <BrowserRouter>{children}</BrowserRouter>
  );
};

export const App: React.FC = () => {
  const theme = useSettingsStore((s) => s.theme);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  useEffect(() => {
    const cleanup = createRealtimeSocket(queryClient);
    return cleanup;
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterComponent>
        <AppRoutes />
      </RouterComponent>
    </QueryClientProvider>
  );
};

export default App;
