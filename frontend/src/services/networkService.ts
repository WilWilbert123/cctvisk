import { api } from './api';
import type {
  NetworkInfoResponse,
  NetworkInterfaceInfo,
  SubnetValidationResult,
  NetworkScan,
  ScanStatusResponse,
  ScanStartRequest,
} from '../types/network';
import type { DashboardSummary } from '../types/device';

export const networkService = {
  getDashboardSummary: () => api.get<DashboardSummary>('/dashboard/summary'),

  getNetworkInfo: () => api.get<NetworkInfoResponse>('/network/info'),

  getInterfaces: async (): Promise<NetworkInterfaceInfo[]> => {
    const res = await api.get<NetworkInterfaceInfo[] | { interfaces: NetworkInterfaceInfo[] }>(
      '/network/interfaces'
    );
    if (Array.isArray(res)) return res;
    return res?.interfaces || [];
  },

  validateSubnet: (subnet_cidr: string) =>
    api.post<SubnetValidationResult>('/network/validate-subnet', { subnet_cidr }),

  startScan: (payload: ScanStartRequest) =>
    api.post<NetworkScan>('/network/scan/start', payload),

  cancelScan: () => api.post<{ cancelled: boolean; message?: string }>('/network/scan/cancel'),

  getScanStatus: () => api.get<ScanStatusResponse>('/network/scan/status'),
};
