import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Radar,
  Sun,
  Moon,
  Monitor,
  Wifi,
  WifiOff,
  Radio,
  ShieldCheck,
  Menu,
} from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useNetworkStore } from '../../store/networkStore';
import { useSettingsStore } from '../../store/settingsStore';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const { theme, cycleTheme } = useTheme();
  const networkInfo = useNetworkStore((s) => s.networkInfo);
  const scanStatus = useNetworkStore((s) => s.scanStatus);
  const wsConnected = useNetworkStore((s) => s.wsConnected);
  const toggleSidebar = useSettingsStore((s) => s.toggleSidebar);

  const ThemeIcon = theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor;

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 lg:px-6 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleSidebar}
          className="hidden lg:inline-flex p-2 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          aria-label="Toggle navigation sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 lg:hidden">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-white block leading-none">
              CCTV Assistant
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              {networkInfo?.subnet_cidr || 'Local LAN'}
            </span>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2.5">
          {networkInfo?.is_connected !== false ? (
            <Badge variant="success" dot>
              <Wifi className="w-3.5 h-3.5 mr-1" />
              <span className="font-mono">
                {networkInfo?.ip_address || 'LAN Active'}
              </span>
              {networkInfo?.subnet_cidr && (
                <span className="text-emerald-600/80 dark:text-emerald-400/80 font-mono ml-1">
                  ({networkInfo.subnet_cidr})
                </span>
              )}
            </Badge>
          ) : (
            <Badge variant="danger" dot>
              <WifiOff className="w-3.5 h-3.5 mr-1" />
              Disconnected
            </Badge>
          )}

          {scanStatus.is_running && (
            <Badge variant="info" className="animate-pulse">
              <Radio className="w-3.5 h-3.5 mr-1 animate-spin" />
              Scanning {Math.round(scanStatus.progress)}%
            </Badge>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        <div
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800"
          title={
            wsConnected
              ? 'Real-time WebSocket stream connected'
              : 'Polling mode active'
          }
        >
          <span
            className={`w-2 h-2 rounded-full ${
              wsConnected ? 'bg-emerald-500' : 'bg-amber-500'
            }`}
          />
          <span>{wsConnected ? 'Live Telemetry' : 'Standard Sync'}</span>
        </div>

        <Button
          size="sm"
          variant={scanStatus.is_running ? 'secondary' : 'primary'}
          leftIcon={<Radar className="w-4 h-4" />}
          onClick={() => navigate('/scanner')}
        >
          <span className="hidden sm:inline">
            {scanStatus.is_running ? 'View Active Scan' : 'Scan Network'}
          </span>
          <span className="sm:hidden">Scan</span>
        </Button>

        <button
          type="button"
          onClick={cycleTheme}
          className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          aria-label={`Switch theme (current: ${theme})`}
          title={`Theme: ${theme.toUpperCase()} (Click to switch)`}
        >
          <ThemeIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
