import React from 'react';
import { Network, Cpu, Router, Shield } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { NetworkInfoResponse } from '../../types/network';

interface NetworkInfoCardProps {
  info?: NetworkInfoResponse | null;
  isLoading?: boolean;
}

export const NetworkInfoCard: React.FC<NetworkInfoCardProps> = ({ info, isLoading }) => {
  if (isLoading) {
    return (
      <Card title="Local Network Telemetry">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3" />
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Active Network Interface"
      subtitle="Automatically detected local LAN interface and subnet scope"
      action={
        <Badge variant={info?.is_connected !== false ? 'success' : 'warning'} dot>
          {info?.connection_type || 'LAN'}
        </Badge>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Network className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>IPv4 Address &amp; CIDR</span>
          </div>
          <p className="text-sm font-mono font-semibold text-slate-900 dark:text-slate-100 mt-1.5">
            {info?.ip_address || '127.0.0.1'}
          </p>
          <p className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-0.5">
            Subnet: {info?.subnet_cidr || 'Not detected'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Router className="w-4 h-4 text-sky-600 dark:text-sky-400" />
            <span>Default Gateway &amp; Mask</span>
          </div>
          <p className="text-sm font-mono font-semibold text-slate-900 dark:text-slate-100 mt-1.5">
            {info?.gateway || 'Local Direct'}
          </p>
          <p className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-0.5">
            Mask: {info?.netmask || '255.255.255.0'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Cpu className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span>Interface &amp; Hardware MAC</span>
          </div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-1.5 truncate">
            {info?.interface_name || 'Primary Adapter'}
          </p>
          <p className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-0.5">
            {info?.mac_address || 'Local Host MAC'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Discovery Capabilities</span>
          </div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-1.5">
            ARP + TCP + ONVIF
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {info?.permissions?.notes || 'Unprivileged & elevated fallback enabled'}
          </p>
        </div>
      </div>
    </Card>
  );
};
