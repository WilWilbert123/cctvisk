import React, { useState } from 'react';
import {
  Activity,
  Play,
  Square,
  RefreshCw,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { MonitoringChart } from '../components/monitoring/MonitoringChart';
import { AlertList } from '../components/monitoring/AlertList';
import {
  useMonitoringStatus,
  useStartMonitoring,
  useStopMonitoring,
  useUpdateMonitoringConfig,
  useCheckNowMonitoring,
} from '../hooks/useMonitoring';

export const Monitoring: React.FC = () => {
  const { data: status, isLoading } = useMonitoringStatus();
  const startMon = useStartMonitoring();
  const stopMon = useStopMonitoring();
  const updateConfig = useUpdateMonitoringConfig();
  const checkNow = useCheckNowMonitoring();

  const [intervalSec, setIntervalSec] = useState<number>(
    status?.interval_seconds || 30
  );

  const handleIntervalChange = (val: number) => {
    setIntervalSec(val);
    updateConfig.mutate({ interval_seconds: val });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Real-Time Device &amp; Camera Health Monitoring
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Continuous ICMP/TCP availability polling, latency tracking, and offline alerts
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <select
            value={status?.interval_seconds || intervalSec}
            onChange={(e) => handleIntervalChange(Number(e.target.value))}
            className="px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
          >
            <option value={15}>Poll Every 15s</option>
            <option value={30}>Poll Every 30s</option>
            <option value={60}>Poll Every 60s</option>
            <option value={300}>Poll Every 5m</option>
          </select>

          <Button
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw className="w-4 h-4" />}
            isLoading={checkNow.isPending}
            onClick={() => checkNow.mutate()}
          >
            Check All Now
          </Button>

          {status?.is_running ? (
            <Button
              variant="danger"
              size="sm"
              leftIcon={<Square className="w-4 h-4" />}
              isLoading={stopMon.isPending}
              onClick={() => stopMon.mutate()}
            >
              Pause Scheduler
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Play className="w-4 h-4" />}
              isLoading={startMon.isPending}
              onClick={() => startMon.mutate()}
            >
              Start Monitoring
            </Button>
          )}
        </div>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500">Monitored Devices</p>
              <p className="text-2xl font-bold font-mono mt-1">
                {status?.total_monitored ?? 0}
              </p>
            </div>
            <Activity className="w-8 h-8 text-blue-600" />
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500">Reachable Online</p>
              <p className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                {status?.online_count ?? 0}
              </p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500">Unreachable Offline</p>
              <p className="text-2xl font-bold font-mono text-red-600 mt-1">
                {status?.offline_count ?? 0}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-600" />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <MonitoringChart data={status?.availability_series || []} />
        </div>
        <div className="lg:col-span-4">
          <AlertList alerts={status?.recent_alerts || []} />
        </div>
      </div>

      <Card
        title="Monitored Node Status Table"
        subtitle="Latency and availability of monitored LAN cameras and recorders"
      >
        {isLoading ? (
          <p className="text-xs text-slate-500 py-8 text-center">
            Loading monitored nodes...
          </p>
        ) : !status?.devices || status.devices.length === 0 ? (
          <p className="text-xs text-slate-500 py-8 text-center">
            No devices currently marked for monitoring. Run a scan or enable monitoring on any device.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {status.devices.map((dev) => (
              <div
                key={dev.id || dev.ip_address}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-semibold">
                    {dev.label || dev.ip_address}
                  </p>
                  <p className="text-xs font-mono text-slate-500">
                    {dev.ip_address} •{' '}
                    {dev.latency_ms ? `${Math.round(dev.latency_ms)}ms` : 'N/A'}
                  </p>
                </div>
                <Badge variant={dev.is_online ? 'success' : 'danger'} dot>
                  {dev.is_online ? 'Online' : 'Offline'}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
