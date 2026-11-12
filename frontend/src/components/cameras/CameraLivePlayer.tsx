import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Square,
  RefreshCw,
  Camera as CameraIcon,
  Maximize2,
  Lock,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  Layers,
  Sliders,
  KeyRound,
  Monitor,
  Video,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  useConnectCamera,
  useCameraStreamStatus,
  useStopCameraStream,
} from '../../hooks/useCameras';
import { cameraService } from '../../services/cameraService';
import type { Camera, CameraConnectResponse } from '../../types/camera';

interface CameraLivePlayerProps {
  camera: Camera;
  isOpen: boolean;
  onClose: () => void;
}

const COMMON_RTSP_PRESETS = [
  { label: 'Auto-Detect (Vendor + ONVIF + Common Paths)', value: '' },
  { label: 'Hikvision Main (/Streaming/Channels/101)', value: '/Streaming/Channels/101' },
  { label: 'Hikvision Sub (/Streaming/Channels/102)', value: '/Streaming/Channels/102' },
  {
    label: 'Dahua / Amcrest Main (/cam/realmonitor?channel=1&subtype=0)',
    value: '/cam/realmonitor?channel=1&subtype=0',
  },
  {
    label: 'Dahua / Amcrest Sub (/cam/realmonitor?channel=1&subtype=1)',
    value: '/cam/realmonitor?channel=1&subtype=1',
  },
  { label: 'Axis (/axis-media/media.amp)', value: '/axis-media/media.amp' },
  { label: 'Reolink Main (/h264Preview_01_main)', value: '/h264Preview_01_main' },
  { label: 'Uniview / ONVIF (/media/video1)', value: '/media/video1' },
  { label: 'Generic Stream 1 (/stream1)', value: '/stream1' },
  { label: 'Generic Live (/live/ch0)', value: '/live/ch0' },
];

export const CameraLivePlayer: React.FC<CameraLivePlayerProps> = ({
  camera,
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const videoContainerRef = useRef<HTMLDivElement | null>(null);
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const localMediaStreamRef = useRef<MediaStream | null>(null);

  const connectMutation = useConnectCamera();
  const stopMutation = useStopCameraStream();

  const [username, setUsername] = useState(camera.saved_username || '');
  const [password, setPassword] = useState('');
  const [rtspPort, setRtspPort] = useState<number>(camera.rtsp_port || 554);
  const [httpPort, setHttpPort] = useState<number>(camera.http_port || 80);
  const [onvifPort, setOnvifPort] = useState<number>(camera.onvif_port || 80);
  const [channel, setChannel] = useState<number>(1);
  const [subtype, setSubtype] = useState<number>(0); // 0 = Main HD, 1 = Sub Stream
  const [protocol, setProtocol] = useState<'auto' | 'rtsp' | 'onvif' | 'http_mjpeg'>('auto');
  const [streamPath, setStreamPath] = useState<string>(camera.rtsp_path || '');
  const [saveCredentials, setSaveCredentials] = useState<boolean>(false);

  const [viewMode, setViewMode] = useState<'mjpeg' | 'snapshot'>('mjpeg');
  const [localSourceMode, setLocalSourceMode] = useState<'none' | 'screen' | 'webcam'>('none');
  const [connectionResult, setConnectionResult] = useState<CameraConnectResponse | null>(
    null
  );
  const [streamError, setStreamError] = useState<string | null>(null);
  const [snapshotTick, setSnapshotTick] = useState<number>(Date.now());
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  const stopLocalMedia = () => {
    if (localMediaStreamRef.current) {
      localMediaStreamRef.current.getTracks().forEach((t) => t.stop());
      localMediaStreamRef.current = null;
    }
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = null;
    }
    setLocalSourceMode('none');
  };

  useEffect(() => {
    if (!isOpen) {
      stopLocalMedia();
    }
    return () => {
      stopLocalMedia();
    };
  }, [isOpen]);

  const startScreenShare = async () => {
    try {
      stopLocalMedia();
      setStreamError(null);
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 30 },
        audio: false,
      });
      localMediaStreamRef.current = stream;
      setLocalSourceMode('screen');
      setIsStreaming(true);
      stream.getVideoTracks()[0]?.addEventListener('ended', () => {
        stopLocalMedia();
      });
      setTimeout(() => {
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      }, 50);
    } catch (err: any) {
      setStreamError(err?.message || 'Screen share permission was cancelled.');
    }
  };

  const startWebcamStream = async () => {
    try {
      stopLocalMedia();
      setStreamError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      localMediaStreamRef.current = stream;
      setLocalSourceMode('webcam');
      setIsStreaming(true);
      setTimeout(() => {
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      }, 50);
    } catch (err: any) {
      setStreamError(err?.message || 'Laptop camera permission was denied or no webcam found.');
    }
  };

  const captureInstantSnapshot = () => {
    if (localSourceMode !== 'none' && localVideoRef.current) {
      const video = localVideoRef.current;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(2, 6, 23, 0.8)';
        ctx.fillRect(0, 0, canvas.width, 38);
        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 14px monospace';
        ctx.fillText(
          `NODE: ${camera.ip_address} | SOURCE: ${localSourceMode.toUpperCase()} | ${new Date().toLocaleString()}`,
          14,
          24
        );
        const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
        const a = document.createElement('a');
        a.href = dataUrl;
        a.download = `snapshot-${camera.ip_address}-${Date.now()}.jpg`;
        a.click();
        return;
      }
    }
    window.open(snapshotDownloadUrl, '_blank', 'noopener,noreferrer');
  };

  const { data: streamStatus } = useCameraStreamStatus(
    camera.id,
    isOpen && isStreaming
  );

  // Automatically attempt connection when modal opens
  useEffect(() => {
    if (isOpen && camera) {
      setRtspPort(camera.rtsp_port || 554);
      setHttpPort(camera.http_port || 80);
      setOnvifPort(camera.onvif_port || 80);
      setStreamPath(camera.rtsp_path || '');
      setStreamError(null);

      handleConnect(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, camera.id]);

  // Continuous frame polling interval when streaming (350ms in MJPEG mode, 1000ms in Snapshot mode)
  // Using frame-synced JPEG endpoints avoids Vite HTTP proxy buffering on multipart streams.
  useEffect(() => {
    if (!isOpen || !isStreaming || localSourceMode !== 'none') return;
    const intervalMs = viewMode === 'mjpeg' ? 400 : 1000;
    const timer = setInterval(() => {
      setSnapshotTick(Date.now());
    }, intervalMs);
    return () => clearInterval(timer);
  }, [isOpen, isStreaming, viewMode, localSourceMode]);

  const handleConnect = (isAutoAttempt = false) => {
    setStreamError(null);
    connectMutation.mutate(
      {
        id: camera.id,
        payload: {
          username: username.trim() || undefined,
          password: password || undefined,
          rtsp_port: Number(rtspPort) || 554,
          http_port: Number(httpPort) || 80,
          onvif_port: Number(onvifPort) || 80,
          stream_path: streamPath.trim() || undefined,
          channel,
          subtype,
          protocol,
          save_credentials: saveCredentials,
        },
      },
      {
        onSuccess: (res) => {
          setConnectionResult(res);
          if (res.connected) {
            setIsStreaming(true);
            if (res.camera_reachable === false || res.stream_type === 'snapshot_polling') {
              setViewMode('snapshot');
            } else {
              setViewMode('mjpeg');
            }
            setSnapshotTick(Date.now());
            if (res.camera_reachable === false && !res.requires_auth) {
              setStreamError(
                `No RTSP camera responded on ${camera.ip_address}:${rtspPort}. Showing live Host Screen / Telemetry feed (or click Share Screen / Laptop Camera below).`
              );
            }
          } else {
            setIsStreaming(false);
            if (!isAutoAttempt || res.requires_auth) {
              setStreamError(
                res.message ||
                  'Camera requires credentials or custom RTSP port/path. Enter credentials below and click Connect Live Stream.'
              );
            }
          }
        },
        onError: (err: Error) => {
          setIsStreaming(false);
          if (!isAutoAttempt) {
            setStreamError(err.message);
          }
        },
      }
    );
  };

  const handleStop = () => {
    stopLocalMedia();
    stopMutation.mutate(camera.id);
    setIsStreaming(false);
  };

  const handleFullscreen = () => {
    if (videoContainerRef.current && videoContainerRef.current.requestFullscreen) {
      videoContainerRef.current.requestFullscreen().catch(() => {});
    }
  };

  const activeStreamSrc = (() => {
    if (!isStreaming) return '';
    const baseSnap =
      connectionResult?.snapshot_url ||
      cameraService.getDefaultSnapshotUrl(camera.id, channel, subtype);
    return `${baseSnap}${baseSnap.includes('?') ? '&' : '?'}t=${snapshotTick}`;
  })();

  const snapshotDownloadUrl =
    connectionResult?.snapshot_url ||
    cameraService.getDefaultSnapshotUrl(camera.id, channel, subtype);

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        onClose();
      }}
      title={`Live CCTV Stream — ${camera.label || camera.ip_address}`}
      subtitle={`Target IP: ${camera.ip_address} | Vendor: ${
        camera.manufacturer || camera.vendor || 'ONVIF/RTSP Camera'
      } | Model: ${camera.model || 'Standard IP Camera'}`}
      size="2xl"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: 16:9 Live Video Player Viewport (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          <div
            ref={videoContainerRef}
            className="relative aspect-video w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center shadow-inner"
          >
            {localSourceMode !== 'none' ? (
              <video
                ref={localVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-contain bg-black"
              />
            ) : isStreaming && activeStreamSrc ? (
              <img
                src={activeStreamSrc}
                alt={`Live feed from ${camera.ip_address}`}
                onError={() =>
                  setStreamError(
                    'Video stream interrupted. Click Share Screen or Laptop Camera below, or verify RTSP credentials.'
                  )
                }
                className="w-full h-full object-contain bg-black"
              />
            ) : (
              <div className="p-6 text-center max-w-md space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-blue-400">
                  <CameraIcon className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-semibold text-white">
                  {connectMutation.isPending
                    ? 'Negotiating RTSP / ONVIF Handshake...'
                    : 'Ready to Connect Live Camera Stream'}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {streamError ||
                    'Click Share Screen or Laptop Camera below for live local video, or connect to an RTSP camera.'}
                </p>
              </div>
            )}

            {/* Top HUD Overlay */}
            <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md bg-slate-950/80 text-white text-xs font-mono backdrop-blur-xs border border-white/10">
                  {camera.ip_address}:{rtspPort}
                </span>
                {isStreaming && !streamError && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-600/90 text-white text-xs font-semibold tracking-wider uppercase">
                    <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                    LIVE {viewMode === 'mjpeg' ? 'STREAM' : 'SNAPSHOT 1FPS'}
                  </span>
                )}
              </div>

              {streamStatus?.active && (
                <span className="px-2.5 py-1 rounded-md bg-slate-950/80 text-emerald-400 text-xs font-mono border border-white/10">
                  {streamStatus.fps ? `${streamStatus.fps.toFixed(1)} FPS` : 'Connected'} •{' '}
                  {streamStatus.frames_served} frames
                </span>
              )}
            </div>
          </div>

          {/* Player Control Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                size="sm"
                variant={isStreaming ? 'success' : 'primary'}
                leftIcon={<Play className="w-4 h-4" />}
                isLoading={connectMutation.isPending}
                onClick={() => handleConnect(false)}
              >
                {isStreaming ? 'Reconnect Stream' : 'Connect Live Stream'}
              </Button>

              {isStreaming && (
                <Button
                  size="sm"
                  variant="danger"
                  leftIcon={<Square className="w-4 h-4" />}
                  onClick={handleStop}
                >
                  Stop
                </Button>
              )}

              <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-900">
                <button
                  type="button"
                  onClick={() => {
                    stopLocalMedia();
                    setViewMode('mjpeg');
                    setStreamError(null);
                    setSnapshotTick(Date.now());
                  }}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    localSourceMode === 'none' && viewMode === 'mjpeg'
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  MJPEG Stream
                </button>
                <button
                  type="button"
                  onClick={() => {
                    stopLocalMedia();
                    setViewMode('snapshot');
                    setStreamError(null);
                    setSnapshotTick(Date.now());
                  }}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    localSourceMode === 'none' && viewMode === 'snapshot'
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  Snapshot (1s)
                </button>
              </div>

              <Button
                size="xs"
                variant={localSourceMode === 'screen' ? 'primary' : 'outline'}
                leftIcon={<Monitor className="w-3.5 h-3.5" />}
                onClick={startScreenShare}
              >
                Share Screen
              </Button>

              <Button
                size="xs"
                variant={localSourceMode === 'webcam' ? 'primary' : 'outline'}
                leftIcon={<Video className="w-3.5 h-3.5" />}
                onClick={startWebcamStream}
              >
                Laptop Camera
              </Button>
            </div>

            <div className="flex items-center gap-1.5">
              <Button
                size="xs"
                variant="outline"
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                onClick={() => {
                  setStreamError(null);
                  setSnapshotTick(Date.now());
                }}
              >
                Refresh
              </Button>

              <Button
                size="xs"
                variant="outline"
                leftIcon={<CameraIcon className="w-3.5 h-3.5" />}
                onClick={captureInstantSnapshot}
              >
                Snapshot
              </Button>

              <Button
                size="xs"
                variant="outline"
                onClick={handleFullscreen}
                title="Fullscreen Video"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          {/* Connection Diagnostics Box */}
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                Stream Diagnostics &amp; Masked RTSP Endpoint
              </span>
              {connectionResult?.connected && connectionResult?.camera_reachable !== false ? (
                <Badge variant="success" dot>
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Handshake Verified
                </Badge>
              ) : (
                <Badge variant="warning">
                  {connectionResult?.camera_reachable === false
                    ? 'No RTSP Service on Port ' + rtspPort
                    : 'Awaiting Handshake'}
                </Badge>
              )}
            </div>
            <div className="font-mono text-[11px] text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800 break-all">
              {connectionResult?.resolved_rtsp_uri_masked ||
                camera.rtsp_url_masked ||
                `rtsp://***:***@${camera.ip_address}:${rtspPort}${
                  streamPath || '/Streaming/Channels/101'
                }`}
            </div>
            {connectionResult?.message && (
              <p className="text-slate-500 dark:text-slate-400">
                Status: {connectionResult.message}
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Stream Connection Parameters & Credentials (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
                <Sliders className="w-4 h-4 text-blue-600" />
                <span>Camera Stream Authentication</span>
              </div>
              {camera.has_saved_credentials && (
                <Badge variant="success">
                  <Lock className="w-3 h-3 mr-1" />
                  Vault Stored
                </Badge>
              )}
            </div>

            {streamError && (
              <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">{streamError}</p>
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      navigate(`/recovery?deviceId=${camera.device_id || camera.id}`);
                    }}
                    className="underline font-semibold mt-1 inline-flex items-center gap-1"
                  >
                    <KeyRound className="w-3 h-3" />
                    Forgot password? Open Official Recovery Assistant
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Camera Username (optional)
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Leave blank or e.g. admin"
                  className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Camera Password (optional)
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={
                    camera.has_saved_credentials
                      ? 'Using encrypted Vault'
                      : 'Leave blank if no password'
                  }
                  className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Leave username and password blank to connect without a password. If your camera firmware locks RTSP/ONVIF video with 401 Unauthorized and you do not have the password, use the{' '}
              <button
                type="button"
                onClick={() => {
                  onClose();
                  navigate(`/recovery?deviceId=${camera.device_id || camera.id}`);
                }}
                className="text-blue-600 dark:text-blue-400 underline font-medium"
              >
                Official Recovery Assistant
              </button>
              .
            </p>

            <div className="grid grid-cols-3 gap-2.5">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Channel
                </label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(Number(e.target.value))}
                  className="w-full px-2.5 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                >
                  {Array.from({ length: 16 }, (_, i) => i + 1).map((ch) => (
                    <option key={ch} value={ch}>
                      Channel {ch}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Stream Quality
                </label>
                <select
                  value={subtype}
                  onChange={(e) => setSubtype(Number(e.target.value))}
                  className="w-full px-2.5 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                >
                  <option value={0}>Main Stream (HD)</option>
                  <option value={1}>Sub-Stream (Fast)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Protocol
                </label>
                <select
                  value={protocol}
                  onChange={(e) => setProtocol(e.target.value as any)}
                  className="w-full px-2.5 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                >
                  <option value="auto">Auto (ONVIF/RTSP)</option>
                  <option value="rtsp">RTSP Direct</option>
                  <option value="onvif">ONVIF Profile</option>
                  <option value="http_mjpeg">HTTP Snapshot/MJPEG</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Vendor RTSP Path Preset
              </label>
              <select
                value={
                  COMMON_RTSP_PRESETS.some((p) => p.value === streamPath)
                    ? streamPath
                    : 'custom'
                }
                onChange={(e) => {
                  if (e.target.value !== 'custom') {
                    setStreamPath(e.target.value);
                  }
                }}
                className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 mb-2"
              >
                {COMMON_RTSP_PRESETS.map((preset) => (
                  <option key={preset.label} value={preset.value}>
                    {preset.label}
                  </option>
                ))}
                <option value="custom">Custom RTSP Path...</option>
              </select>

              <input
                type="text"
                value={streamPath}
                onChange={(e) => setStreamPath(e.target.value)}
                placeholder="Optional custom path e.g. /Streaming/Channels/101"
                className="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-[11px] text-slate-500 mb-0.5">
                  RTSP Port
                </label>
                <input
                  type="number"
                  value={rtspPort}
                  onChange={(e) => setRtspPort(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 mb-0.5">
                  HTTP Port
                </label>
                <input
                  type="number"
                  value={httpPort}
                  onChange={(e) => setHttpPort(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 mb-0.5">
                  ONVIF Port
                </label>
                <input
                  type="number"
                  value={onvifPort}
                  onChange={(e) => setOnvifPort(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
            </div>

            <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={saveCredentials}
                onChange={(e) => setSaveCredentials(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              <span>Save credentials in local AES-GCM Encrypted Vault</span>
            </label>

            <Button
              variant="primary"
              className="w-full"
              leftIcon={<Play className="w-4 h-4" />}
              isLoading={connectMutation.isPending}
              onClick={() => handleConnect(false)}
            >
              Connect &amp; Start Live View
            </Button>
          </div>

          {/* Detected ONVIF Media Profiles */}
          {(connectionResult?.media_profiles?.length ||
            camera.media_profiles?.length) ? (
            <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
                <Layers className="w-4 h-4 text-blue-600" />
                <span>ONVIF Media Profiles</span>
              </div>
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {(connectionResult?.media_profiles || camera.media_profiles || []).map(
                  (prof) => (
                    <div
                      key={prof.token}
                      className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-50 dark:bg-slate-800/70"
                    >
                      <span className="font-medium">{prof.name}</span>
                      <span className="font-mono text-slate-500">
                        {prof.resolution || prof.encoding || prof.token}
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          ) : null}

          <div className="flex items-center justify-between gap-2 text-xs">
            <a
              href={camera.admin_url || `http://${camera.ip_address}:${httpPort}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open Camera Web Admin ({camera.ip_address}:{httpPort})
            </a>

            <button
              type="button"
              onClick={() => {
                onClose();
                navigate(`/recovery?deviceId=${camera.device_id || camera.id}`);
              }}
              className="inline-flex items-center gap-1 text-slate-600 dark:text-slate-400 hover:text-blue-600"
            >
              <KeyRound className="w-3.5 h-3.5" />
              Recovery Guide
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
