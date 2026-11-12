import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Radar,
  Server,
  Cctv,
  HardDrive,
  Activity,
  CheckCircle2,
  XCircle,
  Play,
  ArrowRight,
  Plus,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
} from 'recharts';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { NetworkStatus } from '../components/network/NetworkStatus';
import { ScanProgress } from '../components/network/ScanProgress';
import { DeviceCard } from '../components/devices/DeviceCard';
import { DeviceDetails } from '../components/devices/DeviceDetails';
import {
  useDashboardSummary,
  useStartScan,
  useCancelScan,
} from '../hooks/useNetwork';
import { useNetworkStore } from '../store/networkStore';
import type { Device } from '../types/device';

const PIE_COLORS = ['#2563EB', '#16A34A', '#D97706', '#0284C7', '#64748B'];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useDashboardSummary();
  const networkInfo = useNetworkStore((s) => s.networkInfo);
  const scanStatus = useNetworkStore((s) => s.scanStatus);
  const startScan = useStartScan();
  const cancelScan = useCancelScan();

  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  const handleQuickScan = () => {
    startScan.mutate({
      subnet_cidr: summary?.network?.subnet_cidr || networkInfo?.subnet_cidr || undefined,
      interface_name:
        summary?.network?.interface_name || networkInfo?.interface_name || undefined,
      authorized_confirmation: true,
      scan_ports: true,
      enable_onvif: true,
      enable_mdns: true,
      enable_ssdp: true,
    });
  };

  const counts = summary?.counts || {
    total_devices: 0,
    online_devices: 0,
    offline_devices: 0,
    cameras_count: 0,
    nvr_dvr_count: 0,
    unknown_devices: 0,
    monitored_devices: 0,
  };

  const kpiCards = [
    {
      label: 'Total LAN Devices',
      value: counts.total_devices,
      sub: `${counts.online_devices} online / ${counts.offline_devices} offline`,
      icon: Server,
      color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/60 dark:text-blue-400',
      onClick: () => navigate('/devices'),
    },
    {
      label: 'CCTV IP Cameras',
      value: counts.cameras_count,
      sub: 'RTSP / ONVIF Live Capable',
      icon: Cctv,
      color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-400',
      onClick: () => navigate('/cameras'),
    },
    {
      label: 'NVR / DVR Recorders',
      value: counts.nvr_dvr_count,
      sub: 'Multi-channel storage hubs',
      icon: HardDrive,
      color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/60 dark:text-amber-400',
      onClick: () => navigate('/nvr'),
    },
    {
      label: 'Monitored Nodes',
      value: counts.monitored_devices,
      sub: 'Continuous health checks',
      icon: Activity,
      color: 'text-sky-600 bg-sky-50 dark:bg-sky-950/60 dark:text-sky-400',
      onClick: () => navigate('/monitoring'),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title & Action Row */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Network &amp; CCTV Command Center
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time LAN discovery, live camera stream connection, and authorized recovery assistant
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="md"
            leftIcon={<Cctv className="w-4 h-4" />}
            onClick={() => navigate('/cameras')}
          >
            Live Cameras ({counts.cameras_count})
          </Button>
          <Button
            variant="primary"
            size="md"
            leftIcon={<Radar className="w-4 h-4" />}
            isLoading={startScan.isPending}
            onClick={
              scanStatus.is_running ? () => navigate('/scanner') : handleQuickScan
            }
          >
            {scanStatus.is_running ? 'Scan Running...' : 'Quick LAN Scan'}
          </Button>
        </div>
      </div>

      {/* Active Network Banner */}
      <NetworkStatus network={summary?.network || networkInfo} />

      {/* Active Scan Progress if running */}
      {scanStatus.is_running && (
        <ScanProgress
          status={scanStatus}
          onCancel={() => cancelScan.mutate()}
          isCancelling={cancelScan.isPending}
        />
      )}

      {/* KPI Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, idx) => (
              <Card key={idx}>
                <Skeleton className="h-5 w-1/2 mb-3" />
                <Skeleton className="h-8 w-1/3" />
              </Card>
            ))
          : kpiCards.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  onClick={item.onClick}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-600 rounded-xl p-5 shadow-xs transition-all cursor-pointer flex items-start justify-between gap-4"
                >
                  <div>
                    <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                      {item.label}
                    </p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1.5 font-mono">
                      {item.value}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {item.sub}
                    </p>
                  </div>
                  <div
                    className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${item.color}`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                </div>
              );
            })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recently Discovered Devices & Cameras (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <Card
            title="Discovered Network & CCTV Devices"
            subtitle="Click any camera to Connect & View Live Stream, or inspect full device fingerprint"
            action={
              <Button
                size="xs"
                variant="ghost"
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                onClick={() => navigate('/devices')}
              >
                View All
              </Button>
            }
          >
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Skeleton className="h-40 w-full" />
                <Skeleton className="h-40 w-full" />
              </div>
            ) : !summary?.recent_devices || summary.recent_devices.length === 0 ? (
              <div className="py-12 px-4 text-center space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
                  <Radar className="w-7 h-7" />
                </div>
                <div className="max-w-md mx-auto">
                  <h4 className="text-base font-semibold text-slate-900 dark:text-white">
                    No Devices Discovered Yet
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Run an authorized local network scan on{' '}
                    <span className="font-mono font-semibold">
                      {summary?.network?.subnet_cidr || 'your LAN'}
                    </span>{' '}
                    to automatically discover IP cameras, NVR/DVR units, and ONVIF streams, or add a camera manually.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3 flex-wrap">
                  <Button
                    variant="primary"
                    size="sm"
                    leftIcon={<Play className="w-4 h-4" />}
                    onClick={handleQuickScan}
                    isLoading={startScan.isPending}
                  >
                    Start Network Scan Now
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    leftIcon={<Plus className="w-4 h-4" />}
                    onClick={() => navigate('/cameras')}
                  >
                    Add Camera Manually
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summary.recent_devices.slice(0, 6).map((device) => (
                  <DeviceCard
                    key={device.id || device.ip_address}
                    device={device}
                    onSelect={setSelectedDevice}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Classification Breakdown & Recent Activity (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <Card
            title="Device Classification"
            subtitle="Distribution by multi-signal fingerprint"
          >
            {!summary?.status_distribution ||
            summary.status_distribution.every((d) => d.value === 0) ? (
              <div className="py-10 text-center text-xs text-slate-500 dark:text-slate-400">
                Scan your network to view device category breakdown.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={summary.status_distribution.filter((d) => d.value > 0)}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={45}
                        outerRadius={70}
                        paddingAngle={4}
                      >
                        {summary.status_distribution
                          .filter((d) => d.value > 0)
                          .map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={PIE_COLORS[index % PIE_COLORS.length]}
                            />
                          ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-2">
                  {summary.status_distribution.map((item, idx) => (
                    <div
                      key={item.name}
                      className="flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full"
                          style={{
                            backgroundColor: PIE_COLORS[idx % PIE_COLORS.length],
                          }}
                        />
                        <span className="text-slate-700 dark:text-slate-300">
                          {item.name}
                        </span>
                      </div>
                      <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                        {item.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          <Card
            title="Recent Telemetry Events"
            subtitle="Latest scan & monitoring updates"
          >
            {!summary?.recent_events || summary.recent_events.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500 dark:text-slate-400">
                No telemetry events logged yet.
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {summary.recent_events.slice(0, 6).map((evt, idx) => (
                  <div
                    key={evt.id || idx}
                    className="flex items-start gap-2.5 text-xs p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60"
                  >
                    {evt.level === 'error' ? (
                      <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 dark:text-slate-200">
                        {evt.title || evt.type}
                      </p>
                      <p className="text-slate-500 dark:text-slate-400 mt-0.5">
                        {evt.message}
                      </p>
                    </div>
                    <Badge variant="outline" size="sm">
                      {evt.timestamp
                        ? new Date(evt.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : 'Now'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      <DeviceDetails
        device={selectedDevice}
        isOpen={Boolean(selectedDevice)}
        onClose={() => setSelectedDevice(null)}
      />
    </div>
  );
};
