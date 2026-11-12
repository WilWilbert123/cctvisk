import React, { useState } from 'react';
import {
  Cctv,
  Play,
  Settings2,
  KeyRound,
  ExternalLink,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { CameraStatus } from './CameraStatus';
import { cameraService } from '../../services/cameraService';
import { useDeleteCamera } from '../../hooks/useCameras';
import { useDeviceStore } from '../../store/deviceStore';
import type { Camera } from '../../types/camera';

interface CameraCardProps {
  camera: Camera;
  onInspect?: (camera: Camera) => void;
  livePreviewInGrid?: boolean;
}

export const CameraCard: React.FC<CameraCardProps> = ({
  camera,
  onInspect,
  livePreviewInGrid = false,
}) => {
  const navigate = useNavigate();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);
  const liveConnection = useDeviceStore((s) => s.liveConnections[camera.id]);
  const deleteCamera = useDeleteCamera();
  const [imgError, setImgError] = useState(false);
  const [refreshTick, setRefreshTick] = useState(() => Date.now());

  React.useEffect(() => {
    if (!camera.is_online) return;
    const timer = window.setInterval(() => {
      setRefreshTick(Date.now());
    }, 1500);
    return () => window.clearInterval(timer);
  }, [camera.is_online]);

  const baseSnapUrl =
    liveConnection?.snapshot_url || cameraService.getDefaultSnapshotUrl(camera.id);
  const previewUrl = `${baseSnapUrl}${baseSnapUrl.includes('?') ? '&' : '?'}t=${refreshTick}`;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-xs hover:border-blue-500/60 transition-all flex flex-col justify-between">
      {/* 16:9 CCTV Video Viewport / Preview Header */}
      <div className="relative aspect-video bg-slate-950 flex items-center justify-center overflow-hidden group">
        {!imgError ? (
          <img
            src={previewUrl}
            alt={camera.label || camera.ip_address}
            onError={() => setImgError(true)}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-400 p-4 text-center">
            <Cctv className="w-10 h-10 text-blue-500/80 mb-2" />
            <span className="text-xs font-mono text-slate-300">
              {camera.ip_address}:{camera.rtsp_port || 554}
            </span>
            <span className="text-[11px] text-slate-500 mt-1">
              {imgError
                ? 'Authentication or RTSP handshake required — Click Connect & View Live'
                : 'Ready for Live RTSP / ONVIF Stream'}
            </span>
          </div>
        )}

        {/* Top Overlay Status Bar */}
        <div className="absolute top-2.5 left-2.5 right-2.5 flex items-center justify-between gap-2 pointer-events-none">
          <span className="px-2 py-0.5 rounded bg-slate-950/80 text-white text-[11px] font-mono backdrop-blur-xs">
            {camera.ip_address}
          </span>
          {(livePreviewInGrid || Boolean(liveConnection)) && !imgError && (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-600/90 text-white text-[10px] font-semibold tracking-wider uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
              LIVE
            </span>
          )}
        </div>

        {/* Center Quick Play Overlay */}
        <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Play className="w-4 h-4" />}
            onClick={() => setActiveLiveCamera(camera)}
          >
            Connect &amp; View Live
          </Button>
          {(livePreviewInGrid || Boolean(liveConnection)) && (
            <button
              type="button"
              onClick={() => {
                setImgError(false);
                setRefreshTick((t) => t + 1);
              }}
              className="p-2 rounded-lg bg-slate-900/90 text-white hover:bg-slate-800"
              title="Reload Stream"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Camera Metadata Body */}
      <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
        <div className="space-y-2.5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {camera.label || camera.hostname || `Camera ${camera.ip_address}`}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {camera.manufacturer || camera.vendor || 'Generic ONVIF/RTSP'} •{' '}
                {camera.model || 'IP Camera'}
              </p>
            </div>
          </div>

          <CameraStatus
            isOnline={camera.is_online}
            streamActive={Boolean(liveConnection?.connected)}
            hasSavedCredentials={camera.has_saved_credentials}
            onvifSupported={camera.onvif_supported}
            rtspSupported={camera.rtsp_supported !== false}
          />

          <div className="grid grid-cols-3 gap-1.5 pt-1 text-[11px] font-mono text-slate-600 dark:text-slate-400">
            <div className="bg-slate-50 dark:bg-slate-800/60 px-2 py-1 rounded">
              RTSP: {camera.rtsp_port || 554}
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/60 px-2 py-1 rounded">
              HTTP: {camera.http_port || 80}
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/60 px-2 py-1 rounded">
              ONVIF: {camera.onvif_port || 80}
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
          <Button
            size="sm"
            variant="primary"
            className="flex-1"
            leftIcon={<Play className="w-4 h-4" />}
            onClick={() => setActiveLiveCamera(camera)}
          >
            Connect &amp; View Live
          </Button>

          {onInspect && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onInspect(camera)}
              title="Camera Details & Settings"
            >
              <Settings2 className="w-4 h-4" />
            </Button>
          )}

          <Button
            size="sm"
            variant="ghost"
            onClick={() =>
              navigate(`/recovery?deviceId=${camera.device_id || camera.id}`)
            }
            title="Official Password Recovery Guide"
          >
            <KeyRound className="w-4 h-4" />
          </Button>

          {camera.admin_url && (
            <a
              href={camera.admin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Open Camera Web Admin UI"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}

          <button
            type="button"
            onClick={() => deleteCamera.mutate(camera.id)}
            disabled={deleteCamera.isPending}
            className="p-2 rounded-lg text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50 transition-colors disabled:opacity-50"
            title="Delete Camera Card"
            aria-label="Delete Camera Card"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
