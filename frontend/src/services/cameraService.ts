import { api, getApiBaseUrl } from './api';
import type {
  Camera,
  CameraConnectRequest,
  CameraConnectResponse,
  CameraStreamStatus,
  CreateCameraPayload,
} from '../types/camera';

export const cameraService = {
  getCameras: async (): Promise<{ items: Camera[]; total: number }> => {
    const res = await api.get<{ items: Camera[]; total: number } | Camera[]>('/cameras');
    if (Array.isArray(res)) {
      return { items: res, total: res.length };
    }
    return {
      items: res?.items || [],
      total: res?.total ?? (res?.items?.length || 0),
    };
  },

  getCameraById: (id: number) => api.get<Camera>(`/cameras/${id}`),

  createCamera: (payload: CreateCameraPayload) =>
    api.post<Camera>('/cameras', payload),

  updateCamera: (id: number, payload: Partial<Camera>) =>
    api.patch<Camera>(`/cameras/${id}`, payload),

  deleteCamera: (id: number) =>
    api.delete<{ deleted: boolean; camera_id: number }>(`/cameras/${id}`),

  connectCamera: (id: number, payload: CameraConnectRequest) =>
    api.post<CameraConnectResponse>(`/cameras/${id}/connect`, payload),

  getStreamStatus: (id: number) =>
    api.get<CameraStreamStatus>(`/cameras/${id}/stream/status`),

  stopStream: (id: number) =>
    api.post<{ stopped: boolean; message?: string }>(`/cameras/${id}/stream/stop`),

  getDefaultStreamUrl: (id: number, channel = 1, subtype = 0) =>
    `${getApiBaseUrl()}/cameras/${id}/stream.mjpg?channel=${channel}&subtype=${subtype}`,

  getDefaultSnapshotUrl: (id: number, channel = 1, subtype = 0) =>
    `${getApiBaseUrl()}/cameras/${id}/snapshot.jpg?channel=${channel}&subtype=${subtype}`,
};
