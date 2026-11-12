import React, { useState } from 'react';
import {
  HardDrive,
  Plus,
  Play,
  Layers,
  ExternalLink,
  KeyRound,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import {
  useNVRDevices,
  useCreateNVR,
  useDetectNVRChannels,
} from '../hooks/useDevices';
import { useDeviceStore } from '../store/deviceStore';
import type { NVRDevice } from '../types/device';

export const NVRDevices: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useNVRDevices();
  const createNVR = useCreateNVR();
  const detectChannels = useDetectNVRChannels();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const [addOpen, setAddOpen] = useState(false);
  const [ip, setIp] = useState('');
  const [label, setLabel] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [maxChannels, setMaxChannels] = useState(16);

  const nvrs = data?.items || [];

  const handleAddNVR = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ip.trim()) return;
    createNVR.mutate(
      {
        ip_address: ip.trim(),
        label: label.trim() || undefined,
        manufacturer: manufacturer.trim() || undefined,
        model: model.trim() || undefined,
        max_channels: Number(maxChannels) || 16,
      },
      {
        onSuccess: () => {
          setAddOpen(false);
          setIp('');
          setLabel('');
        },
      }
    );
  };

  const openChannelLive = (nvr: NVRDevice, channelNum: number) => {
    setActiveLiveCamera({
      id: nvr.id,
      device_id: nvr.device_id || nvr.id,
      ip_address: nvr.ip_address,
      label: `${nvr.label || nvr.ip_address} — Channel ${channelNum}`,
      manufacturer: nvr.manufacturer,
      model: nvr.model,
      rtsp_port: nvr.rtsp_port || 554,
      http_port: nvr.http_port || 80,
      onvif_port: nvr.onvif_port || 80,
      rtsp_path: `/Streaming/Channels/${channelNum}01`,
      is_online: nvr.is_online,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            NVR &amp; DVR Recording Systems ({nvrs.length})
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Multi-channel network video recorders, channel discovery, and direct channel streaming
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setAddOpen(true)}
        >
          Register NVR / DVR
        </Button>
      </div>

      {isLoading ? (
        <Card>
          <div className="py-12 text-center text-sm text-slate-500">
            Loading NVR / DVR inventory...
          </div>
        </Card>
      ) : nvrs.length === 0 ? (
        <Card>
          <div className="py-12 text-center space-y-3">
            <HardDrive className="w-10 h-10 text-amber-500 mx-auto" />
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              No NVR or DVR Units Discovered Yet
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              Run a network scan to detect Hikvision, Dahua, Uniview, or ONVIF NVR systems, or register an NVR manually.
            </p>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setAddOpen(true)}
            >
              Add NVR Manually
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {nvrs.map((nvr) => (
            <Card
              key={nvr.id}
              title={nvr.label || `NVR ${nvr.ip_address}`}
              subtitle={`${nvr.manufacturer || 'Network Recorder'} • ${
                nvr.model || `${nvr.max_channels || 16}-Channel NVR`
              }`}
              action={
                <Badge variant={nvr.is_online ? 'success' : 'danger'} dot>
                  {nvr.is_online ? 'Online' : 'Offline'}
                </Badge>
              }
            >
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-2 text-xs font-mono bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg">
                  <div>
                    <span className="text-slate-400 block">IPv4</span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {nvr.ip_address}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Ports</span>
                    <span>
                      RTSP {nvr.rtsp_port || 554} / HTTP {nvr.http_port || 80}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Capacity</span>
                    <span>{nvr.max_channels || 16} Channels</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      Quick Channel Live Stream Selector
                    </span>
                    <Button
                      size="xs"
                      variant="outline"
                      leftIcon={<Layers className="w-3.5 h-3.5" />}
                      isLoading={detectChannels.isPending}
                      onClick={() => detectChannels.mutate({ id: nvr.id })}
                    >
                      Probe Channels
                    </Button>
                  </div>
                  <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5">
                    {Array.from(
                      { length: Math.min(16, nvr.max_channels || 8) },
                      (_, idx) => idx + 1
                    ).map((ch) => (
                      <button
                        key={ch}
                        type="button"
                        onClick={() => openChannelLive(nvr, ch)}
                        className="px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/60 text-xs font-mono font-medium flex items-center justify-center gap-1 transition-colors"
                        title={`Connect Live to Channel ${ch}`}
                      >
                        <Play className="w-2.5 h-2.5 text-blue-600" />
                        CH{ch}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <Button
                    size="xs"
                    variant="primary"
                    leftIcon={<Play className="w-3.5 h-3.5" />}
                    onClick={() => openChannelLive(nvr, 1)}
                  >
                    View Main Stream (CH1)
                  </Button>
                  <div className="flex items-center gap-2">
                    <Button
                      size="xs"
                      variant="ghost"
                      leftIcon={<KeyRound className="w-3.5 h-3.5" />}
                      onClick={() =>
                        navigate(`/recovery?deviceId=${nvr.device_id || nvr.id}`)
                      }
                    >
                      Recovery Guide
                    </Button>
                    <a
                      href={`http://${nvr.ip_address}:${nvr.http_port || 80}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Web Admin
                    </a>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        title="Register NVR / DVR System"
        size="md"
      >
        <form onSubmit={handleAddNVR} className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1">IPv4 Address *</label>
            <input
              type="text"
              required
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="192.168.1.200"
              className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">NVR Label</label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Server Room Primary NVR"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Manufacturer</label>
              <input
                type="text"
                value={manufacturer}
                onChange={(e) => setManufacturer(e.target.value)}
                placeholder="Hikvision / Dahua"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Max Channels</label>
              <select
                value={maxChannels}
                onChange={(e) => setMaxChannels(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              >
                <option value={4}>4 Channels</option>
                <option value={8}>8 Channels</option>
                <option value={16}>16 Channels</option>
                <option value={32}>32 Channels</option>
                <option value={64}>64 Channels</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAddOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createNVR.isPending}
            >
              Save NVR
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
