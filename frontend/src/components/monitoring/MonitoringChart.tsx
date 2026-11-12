import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  CartesianGrid,
} from 'recharts';
import { Card } from '../ui/Card';

interface MonitoringChartProps {
  data: Array<{
    timestamp: string;
    time?: string;
    online: number;
    offline: number;
    avg_latency_ms?: number;
  }>;
}

export const MonitoringChart: React.FC<MonitoringChartProps> = ({ data }) => {
  const formatted = (data || []).map((item) => ({
    ...item,
    label:
      item.time ||
      (item.timestamp
        ? new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Now'),
  }));

  return (
    <Card
      title="Device Availability & Reachability Timeline"
      subtitle="Real-time online vs offline monitored devices on your LAN"
    >
      {formatted.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-sm text-slate-500 dark:text-slate-400">
          No monitoring telemetry samples recorded yet. Start monitoring or run a check now.
        </div>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formatted}>
              <defs>
                <linearGradient id="onlineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#16A34A" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#16A34A" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="offlineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#DC2626" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <RechartsTooltip />
              <Area
                type="monotone"
                dataKey="online"
                name="Online Devices"
                stroke="#16A34A"
                fillOpacity={1}
                fill="url(#onlineGrad)"
              />
              <Area
                type="monotone"
                dataKey="offline"
                name="Offline Devices"
                stroke="#DC2626"
                fillOpacity={1}
                fill="url(#offlineGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
};
