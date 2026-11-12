import { api } from './api';
import type { Device, PaginatedDevices, NVRDevice, NVRChannelInfo } from '../types/device';

export interface DeviceQueryParams {
  search?: string;
  category?: string;
  is_online?: boolean | string;
  confidence?: string;
  sort_by?: string;
  page?: number;
  page_size?: number;
}

export interface CreateDevicePayload {
  ip_address: string;
  label?: string;
  category?: string;
  manufacturer?: string;
  model?: string;
  notes?: string;
}

export interface UpdateDevicePayload {
  label?: string;
  notes?: string;
  is_favorite?: boolean;
  category?: string;
  manufacturer?: string;
  model?: string;
  is_monitored?: boolean;
}

export const deviceService = {
  getDevices: async (params: DeviceQueryParams = {}): Promise<PaginatedDevices> => {
    const queryParams: Record<string, string | number | boolean | undefined> = {
      search: params.search,
      category: params.category !== 'all' ? params.category : undefined,
      confidence: params.confidence !== 'all' ? params.confidence : undefined,
      sort_by: params.sort_by,
      page: params.page || 1,
      page_size: params.page_size || 50,
    };
    if (params.is_online === 'online' || params.is_online === true) {
      queryParams.is_online = true;
    } else if (params.is_online === 'offline' || params.is_online === false) {
      queryParams.is_online = false;
    }

    const res = await api.get<PaginatedDevices | Device[]>('/devices', queryParams);
    if (Array.isArray(res)) {
      return {
        items: res,
        total: res.length,
        page: 1,
        page_size: res.length || 50,
      };
    }
    return {
      items: res?.items || [],
      total: res?.total ?? (res?.items?.length || 0),
      page: res?.page || 1,
      page_size: res?.page_size || 50,
    };
  },

  getDeviceById: (id: number) => api.get<Device>(`/devices/${id}`),

  createDevice: (payload: CreateDevicePayload) =>
    api.post<Device>('/devices', payload),

  updateDevice: (id: number, payload: UpdateDevicePayload) =>
    api.patch<Device>(`/devices/${id}`, payload),

  deleteDevice: (id: number) =>
    api.delete<{ deleted?: boolean; message?: string }>(`/devices/${id}`),

  getNVRDevices: async (): Promise<{ items: NVRDevice[]; total: number }> => {
    const res = await api.get<{ items: NVRDevice[]; total: number } | NVRDevice[]>('/nvr');
    if (Array.isArray(res)) {
      return { items: res, total: res.length };
    }
    return {
      items: res?.items || [],
      total: res?.total ?? (res?.items?.length || 0),
    };
  },

  getNVRById: (id: number) => api.get<NVRDevice>(`/nvr/${id}`),

  createNVR: (payload: {
    ip_address: string;
    label?: string;
    manufacturer?: string;
    model?: string;
    max_channels?: number;
    http_port?: number;
    rtsp_port?: number;
    sdk_port?: number;
    notes?: string;
  }) => api.post<NVRDevice>('/nvr', payload),

  detectNVRChannels: (
    id: number,
    payload?: { username?: string; password?: string; rtsp_port?: number; onvif_port?: number }
  ) =>
    api.post<{
      nvr_id: number;
      ip_address: string;
      max_channels: number;
      detected_channels: NVRChannelInfo[];
      message?: string;
    }>(`/nvr/${id}/detect-channels`, payload || {}),
};
