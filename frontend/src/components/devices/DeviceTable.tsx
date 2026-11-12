import React from 'react';
import { Play, Eye, KeyRound, ExternalLink, Cctv, HardDrive, Server } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Table, type TableColumn } from '../ui/Table';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { DeviceStatus } from './DeviceStatus';
import { useDeviceStore } from '../../store/deviceStore';
import type { Device } from '../../types/device';

interface DeviceTableProps {
  devices: Device[];
  onSelectDevice: (device: Device) => void;
}

export const DeviceTable: React.FC<DeviceTableProps> = ({
  devices,
  onSelectDevice,
}) => {
  const navigate = useNavigate();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const columns: TableColumn<Device>[] = [
    {
      key: 'ip',
      header: 'IP & Hostname',
      render: (d) => (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
            {d.category === 'ip_camera' ? (
              <Cctv className="w-4 h-4" />
            ) : d.category === 'nvr_dvr' ? (
              <HardDrive className="w-4 h-4" />
            ) : (
              <Server className="w-4 h-4" />
            )}
          </div>
          <div>
            <div className="font-mono font-semibold text-slate-900 dark:text-slate-100">
              {d.ip_address}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {d.label || d.hostname || 'Unlabeled Host'}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'vendor',
      header: 'Vendor & MAC',
      render: (d) => (
        <div>
          <div className="font-medium text-slate-800 dark:text-slate-200">
            {d.manufacturer || d.vendor || 'Unknown Vendor'}
          </div>
          <div className="text-xs font-mono text-slate-500 dark:text-slate-400">
            {d.mac_address || 'N/A'}
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Classification',
      render: (d) => (
        <div className="space-y-1">
          <Badge
            variant={
              d.category === 'ip_camera'
                ? 'info'
                : d.category === 'nvr_dvr'
                ? 'warning'
                : 'default'
            }
          >
            {(d.category || 'unknown').replace('_', ' ').toUpperCase()}
          </Badge>
        </div>
      ),
    },
    {
      key: 'ports',
      header: 'Open Ports & Protocols',
      render: (d) => {
        const ports = (d.open_ports || []).map((p) =>
          typeof p === 'number' ? p : p.port
        );
        return (
          <div className="flex flex-wrap gap-1 max-w-xs">
            {ports.length === 0 ? (
              <span className="text-xs text-slate-400">None detected</span>
            ) : (
              ports.slice(0, 5).map((p) => (
                <Badge key={p} variant="outline" size="sm" className="font-mono">
                  {p}
                </Badge>
              ))
            )}
            {(d.protocols || []).map((proto) => (
              <Badge key={proto} variant="info" size="sm">
                {proto}
              </Badge>
            ))}
          </div>
        );
      },
    },
    {
      key: 'status',
      header: 'Status & Confidence',
      render: (d) => (
        <DeviceStatus
          isOnline={d.is_online}
          confidence={d.confidence}
          latencyMs={d.latency_ms}
        />
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (d) => {
        const isCam =
          d.category === 'ip_camera' ||
          Boolean(d.camera) ||
          (d.open_ports || []).some((p) =>
            typeof p === 'number' ? p === 554 : p.port === 554
          );

        return (
          <div
            className="flex items-center gap-1.5"
            onClick={(e) => e.stopPropagation()}
          >
            {isCam && (
              <Button
                size="xs"
                variant="primary"
                leftIcon={<Play className="w-3.5 h-3.5" />}
                onClick={() =>
                  setActiveLiveCamera(
                    d.camera || {
                      id: d.id,
                      device_id: d.id,
                      ip_address: d.ip_address,
                      label: d.label || d.ip_address,
                      manufacturer: d.manufacturer || d.vendor,
                      model: d.model,
                      rtsp_port: 554,
                      http_port: 80,
                      is_online: d.is_online,
                    }
                  )
                }
              >
                Live View
              </Button>
            )}
            <Button
              size="xs"
              variant="outline"
              leftIcon={<Eye className="w-3.5 h-3.5" />}
              onClick={() => onSelectDevice(d)}
            >
              Details
            </Button>
            <Button
              size="xs"
              variant="ghost"
              leftIcon={<KeyRound className="w-3.5 h-3.5" />}
              onClick={() => navigate(`/recovery?deviceId=${d.id}`)}
            >
              Recover
            </Button>
            {d.admin_url && (
              <a
                href={d.admin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600"
                title="Open Web Admin"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <Table
      columns={columns}
      data={devices}
      keyExtractor={(d) => d.id || d.ip_address}
      onRowClick={onSelectDevice}
      emptyMessage="No devices match the current filters. Run a network scan or adjust filters."
    />
  );
};
