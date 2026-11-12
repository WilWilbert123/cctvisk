export interface MediaProfile {
  name: string;
  token: string;
  resolution?: string;
  encoding?: string;
  fps?: number;
  stream_uri_masked?: string;
}

export interface Camera {
  id: number;
  device_id?: number;
  ip_address: string;
  mac_address?: string | null;
  hostname?: string | null;
  label?: string | null;
  manufacturer?: string | null;
  vendor?: string | null;
  model?: string | null;
  firmware_version?: string | null;
  serial_number?: string | null;
  onvif_supported?: boolean;
  rtsp_supported?: boolean;
  http_supported?: boolean;
  rtsp_port: number;
  http_port: number;
  https_port?: number | null;
  onvif_port?: number | null;
  rtsp_path?: string | null;
  rtsp_url_masked?: string | null;
  snapshot_path?: string | null;
  admin_url?: string | null;
  is_online: boolean;
  confidence?: string;
  protocols?: string[];
  open_ports?: number[];
  media_profiles?: MediaProfile[];
  has_saved_credentials?: boolean;
  saved_username?: string | null;
  stream_active?: boolean;
  last_seen?: string | null;
  notes?: string | null;
}

export interface CameraConnectRequest {
  username?: string;
  password?: string;
  rtsp_port?: number;
  http_port?: number;
  onvif_port?: number;
  stream_path?: string;
  channel?: number;
  subtype?: number; // 0 = Main Stream, 1 = Sub Stream
  protocol?: 'auto' | 'rtsp' | 'onvif' | 'http_mjpeg';
  save_credentials?: boolean;
}

export interface CameraConnectResponse {
  connected: boolean;
  camera_reachable?: boolean;
  camera_id: number;
  ip_address: string;
  stream_type: 'mjpeg_proxy' | 'snapshot_polling' | 'direct_mjpeg';
  stream_url: string;
  snapshot_url: string;
  resolved_rtsp_uri_masked: string | null;
  media_profiles: MediaProfile[];
  requires_auth: boolean;
  message: string;
}

export interface CameraStreamStatus {
  active: boolean;
  fps: number;
  frames_served: number;
  last_error: string | null;
  mode: string;
}

export interface CreateCameraPayload {
  ip_address: string;
  label?: string;
  manufacturer?: string;
  model?: string;
  rtsp_port?: number;
  http_port?: number;
  onvif_port?: number;
  rtsp_path?: string;
  username?: string;
  password?: string;
  save_credentials?: boolean;
}
