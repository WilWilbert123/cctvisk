import React from 'react';
import { Bell, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { MonitoringEvent } from '../../types/device';

interface AlertListProps {
  alerts: MonitoringEvent[];
}

export const AlertList: React.FC<AlertListProps> = ({ alerts }) => {
  return (
    <Card
      title="Status Transition Alerts"
      subtitle="Recent device online/offline reachability events"
    >
      {!alerts || alerts.length === 0 ? (
        <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          <Bell className="w-8 h-8 mx-auto text-slate-400 mb-2 opacity-60" />
          No offline transitions or alerts recorded.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-80 overflow-y-auto">
          {alerts.map((alert, idx) => {
            const isOnline =
              alert.is_online === true || alert.status === 'online';
            return (
              <div
                key={alert.id || idx}
                className="flex items-start justify-between gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800"
              >
                <div className="flex items-start gap-2.5">
                  {isOnline ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                      {alert.device_label || alert.ip_address || 'Monitored Device'}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                      {alert.message ||
                        `Device is ${isOnline ? 'online' : 'unreachable'}`}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <Badge variant={isOnline ? 'success' : 'danger'}>
                    {isOnline ? 'ONLINE' : 'OFFLINE'}
                  </Badge>
                  <p className="text-[11px] font-mono text-slate-400 mt-1">
                    {alert.checked_at || alert.timestamp
                      ? new Date(
                          (alert.checked_at || alert.timestamp) as string
                        ).toLocaleTimeString()
                      : ''}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
