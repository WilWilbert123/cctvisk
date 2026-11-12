import React from 'react';
import { Wifi, WifiOff, ShieldCheck, Globe } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { NetworkInfoResponse } from '../../types/network';

interface NetworkStatusProps {
  network?: NetworkInfoResponse | null;
}

export const NetworkStatus: React.FC<NetworkStatusProps> = ({ network }) => {
  const isConnected = network?.is_connected !== false && Boolean(network?.ip_address);

  return (
    <div className="flex flex-wrap items-center gap-3 p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
      <div
        className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
          isConnected
            ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400'
            : 'bg-red-50 text-red-600 dark:bg-red-950/60 dark:text-red-400'
        }`}
      >
        {isConnected ? <Wifi className="w-5 h-5" /> : <WifiOff className="w-5 h-5" />}
      </div>

      <div className="flex-1 min-w-[180px]">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {network?.interface_name || 'Local Network Adapter'}
          </span>
          <Badge variant={isConnected ? 'success' : 'danger'} dot>
            {isConnected ? 'Connected' : 'No LAN Link'}
          </Badge>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
          Host IP: {network?.ip_address || 'Detecting...'} | Subnet:{' '}
          {network?.subnet_cidr || 'N/A'} | Gateway: {network?.gateway || 'N/A'}
        </p>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
        <Globe className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <span>Type: {network?.connection_type || 'Ethernet / Wi-Fi'}</span>
        {network?.ssid && (
          <Badge variant="info">SSID: {network.ssid}</Badge>
        )}
        <Badge variant="outline">
          <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" />
          RFC1918 Private Scope
        </Badge>
      </div>
    </div>
  );
};
