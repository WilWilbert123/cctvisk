import React, { useState } from 'react';
import { History as HistoryIcon, Radar, KeyRound, Activity } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useHistoryData } from '../hooks/useMonitoring';

export const History: React.FC = () => {
  const { scans, recovery, activity } = useHistoryData();
  const [activeTab, setActiveTab] = useState<'scans' | 'recovery' | 'activity'>(
    'scans'
  );

  const scanItems = scans.data || [];
  const recoveryItems = recovery.data || [];
  const activityItems = activity.data || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Scan, Discovery &amp; Recovery Audit History
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Chronological audit log of network scans, discovered CCTV nodes, and official recovery operations
        </p>
      </div>

      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('scans')}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'scans'
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
          }`}
        >
          <Radar className="w-4 h-4" />
          <span>Network Scans ({scanItems.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('recovery')}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'recovery'
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
          }`}
        >
          <KeyRound className="w-4 h-4" />
          <span>Recovery Audit Log ({recoveryItems.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('activity')}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'activity'
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>System Activity ({activityItems.length})</span>
        </button>
      </div>

      {activeTab === 'scans' && (
        <Card title="Historical Network Scan Sessions">
          {scanItems.length === 0 ? (
            <p className="text-xs text-slate-500 py-8 text-center">
              No scan sessions recorded yet.
            </p>
          ) : (
            <div className="space-y-2.5">
              {scanItems.map((s: any) => (
                <div
                  key={s.id}
                  className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <span className="font-mono font-semibold text-sm">
                      {s.subnet_cidr}
                    </span>
                    <p className="text-slate-500 mt-0.5">
                      Started:{' '}
                      {s.started_at
                        ? new Date(s.started_at).toLocaleString()
                        : 'N/A'}{' '}
                      • Devices Found: <strong>{s.devices_found ?? 0}</strong> •
                      Cameras Found: <strong>{s.cameras_found ?? 0}</strong>
                    </p>
                  </div>
                  <Badge
                    variant={
                      s.status === 'completed'
                        ? 'success'
                        : s.status === 'running'
                        ? 'info'
                        : 'default'
                    }
                  >
                    {(s.status || 'completed').toUpperCase()}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'recovery' && (
        <Card title="Password & Firmware Recovery Audit Records">
          {recoveryItems.length === 0 ? (
            <p className="text-xs text-slate-500 py-8 text-center">
              No recovery audit entries logged yet.
            </p>
          ) : (
            <div className="space-y-2.5">
              {recoveryItems.map((rec: any) => (
                <div
                  key={rec.id}
                  className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <p className="font-semibold text-sm">
                      {rec.manufacturer} — {rec.method_used}
                    </p>
                    <p className="text-slate-500 mt-0.5">
                      Device ID #{rec.device_id} • {rec.notes || 'Official procedure'}
                    </p>
                  </div>
                  <Badge variant="info">
                    {(rec.status || 'logged').toUpperCase()}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'activity' && (
        <Card title="System & Monitoring Activity Timeline">
          {activityItems.length === 0 ? (
            <p className="text-xs text-slate-500 py-8 text-center">
              No system activity events recorded yet.
            </p>
          ) : (
            <div className="space-y-2.5">
              {activityItems.map((act: any, idx: number) => (
                <div
                  key={act.id || idx}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-semibold">
                      {act.title || act.event_type || act.type || 'Event'}
                    </span>
                    <p className="text-slate-500 mt-0.5">{act.message}</p>
                  </div>
                  <span className="font-mono text-slate-400">
                    {act.timestamp || act.created_at
                      ? new Date(act.timestamp || act.created_at).toLocaleString()
                      : ''}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
