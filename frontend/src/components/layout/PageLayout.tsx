import React from 'react';
import { Outlet } from 'react-router-dom';
import { X, Info, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MobileNavigation } from './MobileNavigation';
import { useNetworkStore } from '../../store/networkStore';
import { useDeviceStore } from '../../store/deviceStore';
import { useNetworkInfo, useScanStatus } from '../../hooks/useNetwork';
import { CameraLivePlayer } from '../cameras/CameraLivePlayer';

export const PageLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  useNetworkInfo();
  useScanStatus();

  const notifications = useNetworkStore((s) => s.notifications);
  const dismissNotification = useNetworkStore((s) => s.dismissNotification);
  const activeLiveCamera = useDeviceStore((s) => s.activeLiveCamera);
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  return (
    <div className="h-screen overflow-hidden flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        <Header />

        {/* Compact Top Notification Pill */}
        {notifications.length > 0 && (
          <div className="fixed top-2.5 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-1.5 max-w-md w-auto pointer-events-none px-3">
            {notifications.slice(0, 2).map((n) => {
              const Icon =
                n.type === 'success'
                  ? CheckCircle2
                  : n.type === 'warning'
                  ? AlertTriangle
                  : n.type === 'error'
                  ? AlertCircle
                  : Info;
              const borderStyles =
                n.type === 'success'
                  ? 'border-emerald-500/40 bg-emerald-50/95 dark:bg-emerald-950/90 text-emerald-900 dark:text-emerald-100'
                  : n.type === 'warning'
                  ? 'border-amber-500/40 bg-amber-50/95 dark:bg-amber-950/90 text-amber-900 dark:text-amber-100'
                  : n.type === 'error'
                  ? 'border-red-500/40 bg-red-50/95 dark:bg-red-950/90 text-red-900 dark:text-red-100'
                  : 'border-blue-500/40 bg-blue-50/95 dark:bg-blue-950/90 text-blue-900 dark:text-blue-100';

              return (
                <div
                  key={n.id}
                  className={`pointer-events-auto inline-flex items-center gap-2 px-2.5 py-1 rounded-full border shadow-sm backdrop-blur-md text-[11px] leading-tight animate-fade-in ${borderStyles}`}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="font-semibold whitespace-nowrap">{n.title}:</span>
                  <span className="opacity-90 truncate max-w-[260px] sm:max-w-[340px]">
                    {n.message}
                  </span>
                  <button
                    type="button"
                    onClick={() => dismissNotification(n.id)}
                    className="p-0.5 rounded-full opacity-70 hover:opacity-100 shrink-0"
                    aria-label="Dismiss notification"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 lg:p-8 pb-24 lg:pb-8 max-w-[1600px] w-full mx-auto">
          {children || <Outlet />}
        </main>

        <MobileNavigation />
      </div>

      {/* Global Live CCTV Stream Connection & Player Modal */}
      {activeLiveCamera && (
        <CameraLivePlayer
          camera={activeLiveCamera}
          isOpen={Boolean(activeLiveCamera)}
          onClose={() => setActiveLiveCamera(null)}
        />
      )}
    </div>
  );
};
