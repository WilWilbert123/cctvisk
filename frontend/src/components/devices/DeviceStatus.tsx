import React from 'react';
import { Badge } from '../ui/Badge';
import type { ConfidenceLevel } from '../../types/device';

interface DeviceStatusProps {
  isOnline: boolean;
  confidence?: ConfidenceLevel;
  latencyMs?: number | null;
}

export const DeviceStatus: React.FC<DeviceStatusProps> = ({
  isOnline,
  confidence,
  latencyMs,
}) => {
  const normConf = (confidence || '').toUpperCase();

  return (
    <div className="inline-flex items-center gap-2 flex-wrap">
      <Badge variant={isOnline ? 'success' : 'danger'} dot>
        {isOnline ? 'Online' : 'Offline'}
      </Badge>

      {latencyMs !== undefined && latencyMs !== null && isOnline && (
        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
          {Math.round(latencyMs)}ms
        </span>
      )}

      {normConf && (
        <Badge
          variant={
            normConf === 'HIGH'
              ? 'info'
              : normConf === 'MEDIUM'
              ? 'warning'
              : 'outline'
          }
        >
          {normConf} CONFIDENCE
        </Badge>
      )}
    </div>
  );
};
