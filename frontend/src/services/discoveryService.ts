import { api } from './api';
import type { DiscoveryResultsResponse, PortInfo } from '../types/network';

export const discoveryService = {
  getResults: () => api.get<DiscoveryResultsResponse>('/discovery/results'),

  runProbe: (methods: string[] = ['onvif', 'mdns', 'ssdp', 'http']) =>
    api.post<DiscoveryResultsResponse>('/discovery/probe', { methods }),

  getCommonPorts: async (): Promise<PortInfo[]> => {
    const res = await api.get<PortInfo[] | { ports: PortInfo[] }>('/ports/common');
    if (Array.isArray(res)) return res;
    return res?.ports || [];
  },

  scanPorts: (ip_address: string, ports?: number[]) =>
    api.post<{
      ip_address: string;
      open_ports: PortInfo[];
      total_scanned: number;
      scan_duration_ms?: number;
    }>('/ports/scan', { ip_address, ports }),

  discoverOnvif: () =>
    api.post<{
      devices: Array<{
        ip_address: string;
        port?: number;
        manufacturer?: string;
        model?: string;
        xaddrs?: string[];
        scopes?: string[];
      }>;
      count: number;
    }>('/onvif/discover'),

  interrogateOnvif: (payload: {
    ip_address: string;
    port?: number;
    username?: string;
    password?: string;
  }) =>
    api.post<{
      ip_address: string;
      reachable: boolean;
      authenticated?: boolean;
      manufacturer?: string;
      model?: string;
      firmware_version?: string;
      serial_number?: string;
      hardware_id?: string;
      media_profiles?: Array<{
        name: string;
        token: string;
        resolution?: string;
        encoding?: string;
        stream_uri_masked?: string;
      }>;
      message?: string;
    }>('/onvif/interrogate', payload),
};
