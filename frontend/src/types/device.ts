import type { Camera } from './camera';

export type DeviceCategory =
  | 'ip_camera'
  | 'nvr_dvr'
  | 'network_infrastructure'
  | 'workstation_mobile'
  | 'unknown'
  | string;

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'high' | 'medium' | 'low' | string;

export interface OpenPortRecord {
  id?: number;
  port: number;
  protocol: string;
  service_name?: string;
  service?: string;
  state?: string;
  banner?: string | null;
}

export interface MonitoringEvent {
  id?: number;
  device_id?: number;
  ip_address?: string;
  device_label?: string;
  status?: 'online' | 'offline' | string;
  is_online?: boolean;
  latency_ms?: number | null;
  event_type?: string;
  message?: string;
  checked_at?: string;
  timestamp?: string;
}

export interface NVRChannelInfo {
  channel: number;
  name: string;
  status: 'online' | 'offline' | 'configured' | string;
  rtsp_path?: string;
  resolution?: string;
}

export interface NVRDevice {
  id: number;
  device_id?: number;
  ip_address: string;
  label?: string | null;
  hostname?: string | null;
  mac_address?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  firmware_version?: string | null;
  max_channels: number;
  active_channels?: number;
  channels?: NVRChannelInfo[];
  http_port: number;
  rtsp_port: number;
  sdk_port?: number | null;
  onvif_port?: number | null;
  is_online: boolean;
  last_seen?: string | null;
  notes?: string | null;
}

export interface Device {
  id: number;
  ip_address: string;
  mac_address?: string | null;
  hostname?: string | null;
  label?: string | null;
  vendor?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  category: DeviceCategory;
  device_type?: string | null;
  confidence: ConfidenceLevel;
  confidence_score?: number;
  is_online: boolean;
  is_monitored?: boolean;
  is_favorite?: boolean;
  latency_ms?: number | null;
  first_seen?: string;
  last_seen?: string;
  notes?: string | null;
  open_ports?: Array<number | OpenPortRecord>;
  protocols?: string[];
  discovery_methods?: string[];
  classification_evidence?: string[];
  onvif_available?: boolean;
  rtsp_available?: boolean;
  http_title?: string | null;
  http_server?: string | null;
  admin_url?: string | null;
  camera?: Camera | null;
  nvr?: NVRDevice | null;
  monitoring_records?: MonitoringEvent[];
}

export interface PaginatedDevices {
  items: Device[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  network: {
    interface_name: string;
    ip_address: string;
    subnet_cidr: string;
    netmask: string;
    gateway: string | null;
    mac_address: string | null;
    is_connected: boolean;
    connection_type: string;
    ssid: string | null;
  };
  counts: {
    total_devices: number;
    online_devices: number;
    offline_devices: number;
    cameras_count: number;
    nvr_dvr_count: number;
    unknown_devices: number;
    monitored_devices: number;
  };
  latest_scan: {
    id: number;
    subnet_cidr: string;
    status: string;
    progress: number;
    devices_found: number;
    cameras_found: number;
    started_at: string;
    completed_at?: string | null;
  } | null;
  recent_devices: Device[];
  monitoring_activity: MonitoringEvent[];
  status_distribution: Array<{
    name: string;
    value: number;
    category: string;
  }>;
  recent_events: Array<{
    id?: number;
    type: string;
    title?: string;
    message: string;
    timestamp: string;
    level?: string;
  }>;
}

export interface MonitoringStatusResponse {
  is_running: boolean;
  interval_seconds: number;
  timeout_ms: number;
  total_monitored: number;
  online_count: number;
  offline_count: number;
  devices: Array<{
    id: number;
    device_id?: number;
    ip_address: string;
    label?: string | null;
    manufacturer?: string | null;
    category?: string;
    is_online: boolean;
    latency_ms?: number | null;
    uptime_percent?: number;
    last_checked?: string | null;
  }>;
  availability_series: Array<{
    timestamp: string;
    time?: string;
    online: number;
    offline: number;
    avg_latency_ms?: number;
  }>;
  recent_alerts: MonitoringEvent[];
}
