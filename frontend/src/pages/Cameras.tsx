import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cctv,
  Plus,
  LayoutGrid,
  Radar,
  Search,
  Video,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { CameraCard } from '../components/cameras/CameraCard';
import { CameraDetails } from '../components/cameras/CameraDetails';
import { useCameras, useCreateCamera } from '../hooks/useCameras';
import { useDeviceStore } from '../store/deviceStore';
import type { Camera } from '../types/camera';

export const Cameras: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useCameras();
  const createCamera = useCreateCamera();
  const multiGridActive = useDeviceStore((s) => s.multiGridActive);
  const setMultiGridActive = useDeviceStore((s) => s.setMultiGridActive);
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const [search, setSearch] = useState('');
  const [inspectCamera, setInspectCamera] = useState<Camera | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  const [ipAddress, setIpAddress] = useState('');
  const [label, setLabel] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [rtspPort, setRtspPort] = useState(554);
  const [httpPort, setHttpPort] = useState(80);
  const [onvifPort, setOnvifPort] = useState(80);
  const [rtspPath, setRtspPath] = useState('');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [saveCredentials, setSaveCredentials] = useState(true);

  const cameras = (data?.items || []).filter((cam) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      cam.ip_address.toLowerCase().includes(q) ||
      (cam.label || '').toLowerCase().includes(q) ||
      (cam.manufacturer || '').toLowerCase().includes(q) ||
      (cam.model || '').toLowerCase().includes(q)
    );
  });

  const handleCreateCamera = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ipAddress.trim()) return;
    createCamera.mutate(
      {
        ip_address: ipAddress.trim(),
        label: label.trim() || undefined,
        manufacturer: manufacturer.trim() || undefined,
        model: model.trim() || undefined,
        rtsp_port: Number(rtspPort) || 554,
        http_port: Number(httpPort) || 80,
        onvif_port: Number(onvifPort) || 80,
        rtsp_path: rtspPath.trim() || undefined,
        username: username.trim() || undefined,
        password: password || undefined,
        save_credentials: saveCredentials,
      },
      {
        onSuccess: (createdCam) => {
          setAddOpen(false);
          setIpAddress('');
          setLabel('');
          setPassword('');
          // Immediately open Live Viewer for the newly added camera
          setActiveLiveCamera(createdCam);
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            CCTV Cameras &amp; Live Stream Matrix ({cameras.length})
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Connect to any discovered or registered CCTV camera on your LAN and view live video via RTSP/ONVIF
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant={multiGridActive ? 'success' : 'outline'}
            size="sm"
            leftIcon={<LayoutGrid className="w-4 h-4" />}
            onClick={() => setMultiGridActive(!multiGridActive)}
          >
            {multiGridActive
              ? 'Multi-Camera Live Grid: ON'
              : 'Enable Multi-Camera Live Grid'}
          </Button>

          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setAddOpen(true)}
          >
            Add &amp; Connect Camera
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter cameras by IP address, label, manufacturer, or model..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Video className="w-4 h-4 text-blue-600" />
            <span>
              Click <strong>Connect &amp; View Live</strong> on any camera card to authenticate and view live RTSP/MJPEG stream.
            </span>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <Card>
          <div className="py-12 text-center text-sm text-slate-500">
            Loading CCTV cameras...
          </div>
        </Card>
      ) : cameras.length === 0 ? (
        <Card>
          <div className="py-14 px-4 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
              <Cctv className="w-7 h-7" />
            </div>
            <div className="max-w-md mx-auto">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                No CCTV Cameras Found Yet
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Scan your local network to automatically discover ONVIF and RTSP cameras, or add a camera by IP address to connect and view its live stream right away.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Radar className="w-4 h-4" />}
                onClick={() => navigate('/scanner')}
              >
                Scan Network for Cameras
              </Button>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => setAddOpen(true)}
              >
                Add Camera by IP
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {cameras.map((cam) => (
            <CameraCard
              key={cam.id || cam.ip_address}
              camera={cam}
              onInspect={setInspectCamera}
              livePreviewInGrid={multiGridActive}
            />
          ))}
        </div>
      )}

      <CameraDetails
        camera={inspectCamera}
        isOpen={Boolean(inspectCamera)}
        onClose={() => setInspectCamera(null)}
      />

      {/* Add & Connect Camera Modal */}
      <Modal
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        title="Add & Connect CCTV Camera"
        subtitle="Register an IP camera on your LAN and immediately launch the Live Stream Player"
        size="lg"
      >
        <form onSubmit={handleCreateCamera} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Camera IPv4 Address *
              </label>
              <input
                type="text"
                required
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
                placeholder="192.168.1.64"
                className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Camera Name / Location Label
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="Front Gate PTZ Camera"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Manufacturer
              </label>
              <input
                type="text"
                value={manufacturer}
                onChange={(e) => setManufacturer(e.target.value)}
                placeholder="Hikvision, Dahua, Axis, Reolink..."
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Model
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="DS-2CD2043G2"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                RTSP Port
              </label>
              <input
                type="number"
                value={rtspPort}
                onChange={(e) => setRtspPort(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                HTTP Port
              </label>
              <input
                type="number"
                value={httpPort}
                onChange={(e) => setHttpPort(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                ONVIF Port
              </label>
              <input
                type="number"
                value={onvifPort}
                onChange={(e) => setOnvifPort(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              RTSP Stream Path (Leave blank for automatic vendor path resolution)
            </label>
            <input
              type="text"
              value={rtspPath}
              onChange={(e) => setRtspPath(e.target.value)}
              placeholder="/Streaming/Channels/101"
              className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>

          <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Camera Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Camera Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password for RTSP stream"
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
              />
            </div>
            <label className="col-span-2 flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={saveCredentials}
                onChange={(e) => setSaveCredentials(e.target.checked)}
                className="rounded border-slate-300 text-blue-600"
              />
              <span>Store encrypted credentials in local Vault for 1-click Live Viewing</span>
            </label>
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
              isLoading={createCamera.isPending}
            >
              Save &amp; Connect Live
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
