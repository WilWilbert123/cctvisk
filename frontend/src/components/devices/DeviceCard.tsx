import React from 'react';
import {
  Cctv,
  HardDrive,
  Router,
  Monitor,
  HelpCircle,
  ExternalLink,
  Play,
  Eye,
  KeyRound,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { DeviceStatus } from './DeviceStatus';
import { useDeviceStore } from '../../store/deviceStore';
import type { Device } from '../../types/device';

interface DeviceCardProps {
  device: Device;
  onSelect?: (device: Device) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, onSelect }) => {
  const navigate = useNavigate();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const isCamera =
    device.category === 'ip_camera' ||
    Boolean(device.camera) ||
    (device.open_ports || []).some((p) =>
      typeof p === 'number' ? p === 554 || p === 8554 : p.port === 554 || p.port === 8554
    );

  const CategoryIcon =
    device.category === 'ip_camera'
      ? Cctv
      : device.category === 'nvr_dvr'
      ? HardDrive
      : device.category === 'network_infrastructure'
      ? Router
      : device.category === 'workstation_mobile'
      ? Monitor
      : HelpCircle;

  const openLiveView = (e: React.MouseEvent) => {
    e.stopPropagation();
    const camObj = device.camera || {
      id: device.id,
      device_id: device.id,
      ip_address: device.ip_address,
      mac_address: device.mac_address,
      hostname: device.hostname,
      label: device.label || `${device.manufacturer || 'IP Camera'} (${device.ip_address})`,
      manufacturer: device.manufacturer || device.vendor,
      model: device.model,
      rtsp_port: 554,
      http_port: 80,
      onvif_port: 80,
      is_online: device.is_online,
      protocols: device.protocols || ['RTSP'],
    };
    setActiveLiveCamera(camObj);
  };

  const portsList = (device.open_ports || []).map((p) =>
    typeof p === 'number' ? p : p.port
  );

  return (
    <div
      onClick={() => onSelect && onSelect(device)}
      className="group bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-600 rounded-xl p-4 shadow-xs transition-all cursor-pointer flex flex-col justify-between gap-4"
    >
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                isCamera
                  ? 'bg-blue-50 text-blue-600 dark:bg-blue-950/70 dark:text-blue-400'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              <CategoryIcon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                {device.label || device.hostname || device.ip_address}
              </h4>
              <p className="text-xs font-mono text-blue-600 dark:text-blue-400">
                {device.ip_address}
              </p>
            </div>
          </div>

          <DeviceStatus
            isOnline={device.is_online}
            latencyMs={device.latency_ms}
          />
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg">
          <div>
            <span className="text-[11px] text-slate-400 block">Vendor / Brand</span>
            <span className="font-medium text-slate-800 dark:text-slate-200 truncate block">
              {device.manufacturer || device.vendor || 'Unidentified'}
            </span>
          </div>
          <div>
            <span className="text-[11px] text-slate-400 block">MAC Address</span>
            <span className="font-mono text-slate-800 dark:text-slate-200 truncate block">
              {device.mac_address || 'N/A'}
            </span>
          </div>
        </div>

        {portsList.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-slate-400 mr-1">Ports:</span>
            {portsList.slice(0, 6).map((port) => (
              <Badge key={port} variant="outline" size="sm" className="font-mono">
                {port}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2 flex-wrap">
        {isCamera ? (
          <Button
            size="xs"
            variant="primary"
            leftIcon={<Play className="w-3.5 h-3.5" />}
            onClick={openLiveView}
          >
            Connect &amp; View Live
          </Button>
        ) : (
          <Button
            size="xs"
            variant="outline"
            leftIcon={<Eye className="w-3.5 h-3.5" />}
            onClick={(e) => {
              e.stopPropagation();
              if (onSelect) onSelect(device);
            }}
          >
            Inspect
          </Button>
        )}

        <div className="flex items-center gap-1.5">
          <Button
            size="xs"
            variant="ghost"
            leftIcon={<KeyRound className="w-3.5 h-3.5" />}
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/recovery?deviceId=${device.id}`);
            }}
          >
            Recovery
          </Button>

          {device.admin_url && (
            <a
              href={device.admin_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Open Web Admin Interface"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
