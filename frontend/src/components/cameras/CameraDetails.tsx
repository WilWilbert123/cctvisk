import React, { useState } from 'react';
import { Play, Save, KeyRound, ExternalLink, Layers } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { CameraStatus } from './CameraStatus';
import { useUpdateCamera } from '../../hooks/useCameras';
import { useDeviceStore } from '../../store/deviceStore';
import type { Camera } from '../../types/camera';

interface CameraDetailsProps {
  camera: Camera | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CameraDetails: React.FC<CameraDetailsProps> = ({
  camera,
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const updateCamera = useUpdateCamera();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const [label, setLabel] = useState(camera?.label || '');
  const [manufacturer, setManufacturer] = useState(camera?.manufacturer || '');
  const [model, setModel] = useState(camera?.model || '');
  const [rtspPort, setRtspPort] = useState(camera?.rtsp_port || 554);
  const [httpPort, setHttpPort] = useState(camera?.http_port || 80);
  const [onvifPort, setOnvifPort] = useState(camera?.onvif_port || 80);
  const [rtspPath, setRtspPath] = useState(camera?.rtsp_path || '');

  React.useEffect(() => {
    if (camera) {
      setLabel(camera.label || '');
      setManufacturer(camera.manufacturer || camera.vendor || '');
      setModel(camera.model || '');
      setRtspPort(camera.rtsp_port || 554);
      setHttpPort(camera.http_port || 80);
      setOnvifPort(camera.onvif_port || 80);
      setRtspPath(camera.rtsp_path || '');
    }
  }, [camera]);

  if (!camera) return null;

  const handleSave = () => {
    updateCamera.mutate(
      {
        id: camera.id,
        payload: {
          label,
          manufacturer,
          model,
          rtsp_port: Number(rtspPort) || 554,
          http_port: Number(httpPort) || 80,
          onvif_port: Number(onvifPort) || 80,
          rtsp_path: rtspPath || null,
        },
      },
      {
        onSuccess: () => onClose(),
      }
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={camera.label || `Camera ${camera.ip_address}`}
      subtitle={`IPv4: ${camera.ip_address} | MAC: ${camera.mac_address || 'N/A'}`}
      size="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <Button
            size="sm"
            variant="outline"
            leftIcon={<KeyRound className="w-4 h-4" />}
            onClick={() => {
              onClose();
              navigate(`/recovery?deviceId=${camera.device_id || camera.id}`);
            }}
          >
            Password Recovery Guide
          </Button>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Save className="w-4 h-4" />}
              isLoading={updateCamera.isPending}
              onClick={handleSave}
            >
              Save Camera Config
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
          <CameraStatus
            isOnline={camera.is_online}
            hasSavedCredentials={camera.has_saved_credentials}
            onvifSupported={camera.onvif_supported}
            rtspSupported={camera.rtsp_supported !== false}
          />
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Play className="w-4 h-4" />}
              onClick={() => {
                onClose();
                setActiveLiveCamera(camera);
              }}
            >
              Connect &amp; View Live
            </Button>
            {camera.admin_url && (
              <a
                href={camera.admin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Web UI
              </a>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Camera Label
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
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
              placeholder="Hikvision, Dahua, Axis, Uniview, Reolink..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Model Identifier
            </label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Default RTSP Stream Path
            </label>
            <input
              type="text"
              value={rtspPath}
              onChange={(e) => setRtspPath(e.target.value)}
              placeholder="/Streaming/Channels/101"
              className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
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

        {camera.media_profiles && camera.media_profiles.length > 0 && (
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Detected ONVIF Media Profiles</span>
            </div>
            <div className="space-y-1.5">
              {camera.media_profiles.map((prof) => (
                <div
                  key={prof.token}
                  className="flex items-center justify-between text-xs p-2 rounded bg-white dark:bg-slate-900 border border-slate-200/70 dark:border-slate-800"
                >
                  <span className="font-medium">{prof.name}</span>
                  <div className="flex items-center gap-2">
                    {prof.encoding && <Badge variant="info">{prof.encoding}</Badge>}
                    {prof.resolution && (
                      <Badge variant="outline" className="font-mono">
                        {prof.resolution}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
