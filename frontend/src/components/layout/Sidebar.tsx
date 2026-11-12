import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radar,
  Server,
  Cctv,
  HardDrive,
  Compass,
  Activity,
  KeyRound,
  History,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { useSettingsStore } from '../../store/settingsStore';

interface NavItem {
  to: string;
  label: string;
  icon: React.FC<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/scanner', label: 'Network Scanner', icon: Radar },
  { to: '/cameras', label: 'Cameras & Live View', icon: Cctv },
  { to: '/nvr', label: 'NVR / DVR Systems', icon: HardDrive },
  { to: '/devices', label: 'All Devices', icon: Server },
  { to: '/discovery', label: 'Discovery & ONVIF', icon: Compass },
  { to: '/monitoring', label: 'Monitoring', icon: Activity },
  { to: '/recovery', label: 'Recovery Assistant', icon: KeyRound },
  { to: '/history', label: 'Scan & Audit History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const collapsed = useSettingsStore((s) => s.sidebarCollapsed);

  return (
    <aside
      className={`hidden lg:flex flex-col shrink-0 h-screen sticky top-0 left-0 overflow-hidden select-none bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-200 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div className="h-16 px-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3 shrink-0">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
          <ShieldCheck className="w-5 h-5" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold text-slate-900 dark:text-white truncate">
              CCTV Discovery
            </h1>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
              LAN &amp; Recovery Assistant
            </p>
          </div>
        )}
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-hidden" aria-label="Primary Sidebar Navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            <Icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {!collapsed && (
        <div className="p-4 m-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800">
          <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
            Authorized LAN Boundary
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            Strictly RFC1918 local network discovery, live RTSP/ONVIF viewing, and official recovery guidance.
          </p>
        </div>
      )}
    </aside>
  );
};
