import React, { useState } from 'react';
import {
  Play,
  KeyRound,
  ExternalLink,
  Save,
  Trash2,
  Activity,
  ShieldCheck,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { DeviceStatus } from './DeviceStatus';
import { useUpdateDevice, useDeleteDevice } from '../../hooks/useDevices';
import { useDeviceStore } from '../../store/deviceStore';
import type { Device } from '../../types/device';

interface DeviceDetailsProps {
  device: Device | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DeviceDetails: React.FC<DeviceDetailsProps> = ({
  device,
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const updateDevice = useUpdateDevice();
  const deleteDevice = useDeleteDevice();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const [label, setLabel] = useState(device?.label || '');
  const [notes, setNotes] = useState(device?.notes || '');
  const [isMonitored, setIsMonitored] = useState(Boolean(device?.is_monitored));

  React.useEffect(() => {
    if (device) {
      setLabel(device.label || '');
      setNotes(device.notes || '');
      setIsMonitored(Boolean(device.is_monitored));
    }
  }, [device]);

  if (!device) return null;

  const handleSave = () => {
    updateDevice.mutate(
      {
        id: device.id,
        payload: {
          label,
          notes,
          is_monitored: isMonitored,
        },
      },
      {
        onSuccess: () => onClose(),
      }
    );
  };

  const handleDelete = () => {
    deleteDevice.mutate(device.id, {
      onSuccess: () => onClose(),
    });
  };

  const openLive = () => {
    onClose();
    setActiveLiveCamera(
      device.camera || {
        id: device.id,
        device_id: device.id,
        ip_address: device.ip_address,
        label: device.label || device.ip_address,
        manufacturer: device.manufacturer || device.vendor,
        model: device.model,
        rtsp_port: 554,
        http_port: 80,
        is_online: device.is_online,
      }
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={device.label || device.hostname || `Device ${device.ip_address}`}
      subtitle={`IPv4: ${device.ip_address} | MAC: ${device.mac_address || 'Unknown'}`}
      size="xl"
      footer={
        <div className="w-full flex items-center justify-between gap-2 flex-wrap">
          <Button
            variant="danger"
            size="sm"
            leftIcon={<Trash2 className="w-4 h-4" />}
            isLoading={deleteDevice.isPending}
            onClick={handleDelete}
          >
            Remove Device
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Save className="w-4 h-4" />}
              isLoading={updateDevice.isPending}
              onClick={handleSave}
            >
              Save Changes
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
          <DeviceStatus
            isOnline={device.is_online}
            confidence={device.confidence}
            latencyMs={device.latency_ms}
          />
          <div className="flex items-center gap-2 flex-wrap">
            {device.category === 'CAMERA' ||
            device.category === 'ONVIF_CAMERA' ||
            device.category === 'NVR' ||
            device.category === 'DVR' ||
            device.rtsp_available ||
            device.onvif_available ||
            (device.open_ports || []).includes(554) ? (
              <Button
                size="sm"
                variant="primary"
                leftIcon={<Play className="w-4 h-4" />}
                onClick={openLive}
              >
                Connect &amp; View Live Stream
              </Button>
            ) : (
              <>
                <Badge variant="default" size="sm">
                  Non-Camera ({device.category})
                </Badge>
                <Button
                  size="sm"
                  variant="outline"
                  leftIcon={<Play className="w-4 h-4" />}
                  onClick={openLive}
                >
                  Test RTSP Stream
                </Button>
              </>
            )}
            <Button
              size="sm"
              variant="outline"
              leftIcon={<KeyRound className="w-4 h-4" />}
              onClick={() => {
                onClose();
                navigate(`/recovery?deviceId=${device.id}`);
              }}
            >
              Official Recovery Guide
            </Button>
            {device.admin_url && (
              <a
                href={device.admin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Web Admin
              </a>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-slate-400 block">Manufacturer / OUI</span>
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-1 block">
              {device.manufacturer || device.vendor || 'Unidentified'}
            </span>
          </div>
          <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-slate-400 block">Model / Firmware</span>
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-1 block">
              {device.model || 'Generic Network Device'}
            </span>
          </div>
          <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-slate-400 block">Discovery Methods</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {(device.discovery_methods || ['ARP', 'TCP']).map((m) => (
                <Badge key={m} variant="info" size="sm">
                  {m}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {device.classification_evidence && device.classification_evidence.length > 0 && (
          <div className="p-4 rounded-xl bg-blue-50/50 dark:bg-blue-950/30 border border-blue-200/70 dark:border-blue-900/50 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
              <ShieldCheck className="w-4 h-4" />
              <span>Multi-Signal Classification Evidence</span>
            </div>
            <ul className="list-disc list-inside text-xs text-slate-700 dark:text-slate-300 space-y-1">
              {device.classification_evidence.map((ev, idx) => (
                <li key={idx}>{ev}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Custom Device Label
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. North Gate Bullet Camera"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="flex items-center pt-5">
            <label className="inline-flex items-center gap-2.5 cursor-pointer text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={isMonitored}
                onChange={(e) => setIsMonitored(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <Activity className="w-4 h-4 text-blue-600" />
              <span>Enable Continuous Availability &amp; Latency Monitoring</span>
            </label>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Administrator Notes &amp; Physical Location
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Record physical mounting location, switch port, or maintenance notes..."
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
          />
        </div>
      </div>
    </Modal>
  );
};
