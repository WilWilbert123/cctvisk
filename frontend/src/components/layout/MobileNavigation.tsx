import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radar,
  Cctv,
  Server,
  MoreHorizontal,
  HardDrive,
  Compass,
  Activity,
  KeyRound,
  History,
  Settings,
  X,
} from 'lucide-react';

export const MobileNavigation: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);

  const primaryTabs = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/scanner', label: 'Scan', icon: Radar },
    { to: '/cameras', label: 'Live CCTV', icon: Cctv },
    { to: '/devices', label: 'Devices', icon: Server },
  ];

  const moreLinks = [
    { to: '/nvr', label: 'NVR / DVR Systems', icon: HardDrive },
    { to: '/discovery', label: 'ONVIF & Port Tools', icon: Compass },
    { to: '/monitoring', label: 'Health Monitoring', icon: Activity },
    { to: '/recovery', label: 'Recovery Assistant', icon: KeyRound },
    { to: '/history', label: 'Scan & Audit History', icon: History },
    { to: '/settings', label: 'Settings & Vault', icon: Settings },
  ];

  return (
    <>
      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden bg-slate-950/60 backdrop-blur-xs flex flex-col justify-end">
          <div className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 rounded-t-2xl p-5 pb-24 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                All Modules &amp; Tools
              </span>
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                aria-label="Close mobile menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              {moreLinks.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setDrawerOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 p-3 rounded-xl border text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/70 dark:border-blue-800 dark:text-blue-300'
                        : 'border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0 text-blue-600 dark:text-blue-400" />
                  <span className="truncate">{label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      )}

      <nav
        className="fixed bottom-0 inset-x-0 z-40 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 flex items-center justify-around lg:hidden px-2"
        aria-label="Mobile Bottom Navigation"
      >
        {primaryTabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={() => setDrawerOpen(false)}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-1 py-1.5 px-3 rounded-lg text-[11px] font-medium transition-colors min-w-[64px] ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-slate-500 dark:text-slate-400'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}

        <button
          type="button"
          onClick={() => setDrawerOpen((prev) => !prev)}
          className={`flex flex-col items-center justify-center gap-1 py-1.5 px-3 rounded-lg text-[11px] font-medium transition-colors min-w-[64px] ${
            drawerOpen
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-slate-500 dark:text-slate-400'
          }`}
        >
          <MoreHorizontal className="w-5 h-5" />
          <span>More</span>
        </button>
      </nav>
    </>
  );
};
