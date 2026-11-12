import React from 'react';
import { Radar, StopCircle, CheckCircle2, Cctv, Server } from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import type { ScanStatusResponse } from '../../types/network';

interface ScanProgressProps {
  status: ScanStatusResponse;
  onCancel?: () => void;
  isCancelling?: boolean;
}

export const ScanProgress: React.FC<ScanProgressProps> = ({
  status,
  onCancel,
  isCancelling = false,
}) => {
  const pct = Math.min(100, Math.max(0, Math.round(status.progress || 0)));

  return (
    <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              status.is_running
                ? 'bg-blue-600 text-white animate-pulse'
                : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/70 dark:text-emerald-400'
            }`}
          >
            {status.is_running ? (
              <Radar className="w-5 h-5 animate-spin" />
            ) : (
              <CheckCircle2 className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {status.is_running
                  ? 'Active Multi-Stage Network Scan in Progress'
                  : 'Scan Engine Status'}
              </h4>
              <Badge variant={status.is_running ? 'info' : 'default'}>
                {(status.stage || 'idle').toUpperCase()}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {status.message || 'Ready to discover local devices and CCTV streams'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-4 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200/70 dark:border-slate-700 text-xs">
            <span className="inline-flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
              <Server className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              Devices: <strong className="font-mono">{status.devices_found}</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
              <Cctv className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              Cameras: <strong className="font-mono">{status.cameras_found}</strong>
            </span>
          </div>

          {status.is_running && onCancel && (
            <Button
              variant="danger"
              size="sm"
              leftIcon={<StopCircle className="w-4 h-4" />}
              isLoading={isCancelling}
              onClick={onCancel}
            >
              Stop Scan
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500 dark:text-slate-400">
            Pipeline: ARP / Ping Sweep / Port Fingerprint / ONVIF WS-Discovery / mDNS / SSDP
          </span>
          <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
            {pct}%
          </span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-sky-500 transition-all duration-300 rounded-full"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
};
