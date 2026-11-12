export interface NetworkInterfaceInfo {
  name: string;
  interface_name?: string;
  ip_address: string;
  subnet_cidr: string;
  netmask: string;
  gateway: string | null;
  mac_address: string | null;
  is_up?: boolean;
  is_connected?: boolean;
  connection_type: string;
  ssid?: string | null;
}

export interface NetworkInfoResponse {
  interface_name: string;
  ip_address: string;
  subnet_cidr: string;
  netmask: string;
  gateway: string | null;
  mac_address: string | null;
  is_connected: boolean;
  connection_type: string;
  ssid: string | null;
  dns_servers?: string[];
  interfaces?: NetworkInterfaceInfo[];
  permissions?: {
    raw_socket_available?: boolean;
    arp_available?: boolean;
    is_elevated?: boolean;
    notes?: string;
  };
}

export interface SubnetValidationResult {
  valid: boolean;
  normalized_cidr: string;
  host_count: number;
  message: string;
}

export interface NetworkScan {
  id: number;
  subnet_cidr: string;
  interface_name?: string | null;
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'failed' | string;
  progress: number;
  stage?: string;
  devices_found: number;
  cameras_found: number;
  nvr_found?: number;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  error_message?: string | null;
}

export interface ScanStatusResponse {
  is_running: boolean;
  progress: number;
  stage: string;
  message: string;
  devices_found: number;
  cameras_found: number;
  current_scan: NetworkScan | null;
}

export interface ScanStartRequest {
  subnet_cidr?: string | null;
  interface_name?: string | null;
  authorized_confirmation: boolean;
  scan_ports?: boolean;
  enable_onvif?: boolean;
  enable_mdns?: boolean;
  enable_ssdp?: boolean;
}

export interface DiscoveryResultsResponse {
  onvif: Array<{
    ip_address: string;
    port?: number;
    manufacturer?: string;
    model?: string;
    xaddrs?: string[];
    scopes?: string[];
    endpoint_reference?: string;
    discovered_at?: string;
  }>;
  mdns: Array<{
    ip_address: string;
    hostname?: string;
    service_type?: string;
    service_name?: string;
    port?: number;
    properties?: Record<string, string>;
  }>;
  ssdp: Array<{
    ip_address: string;
    st?: string;
    usn?: string;
    server?: string;
    location?: string;
  }>;
  fingerprints: Array<{
    ip_address: string;
    port?: number;
    server_header?: string;
    title?: string;
    vendor_match?: string;
    confidence?: string;
  }>;
  last_updated: string | null;
}

export interface PortInfo {
  port: number;
  protocol: string;
  service: string;
  description?: string;
  is_open?: boolean;
  banner?: string | null;
  response_time_ms?: number | null;
}
