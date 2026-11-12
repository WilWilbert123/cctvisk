import { api } from './api';
import type {
  ManufacturerRecoveryGuide,
  DeviceRecoveryContext,
  RecoveryRecord,
  SaveVaultCredentialsPayload,
  VaultStatus,
} from '../types/recovery';

export const recoveryService = {
  getAllGuides: async (): Promise<ManufacturerRecoveryGuide[]> => {
    const res = await api.get<
      ManufacturerRecoveryGuide[] | { guides: ManufacturerRecoveryGuide[] }
    >('/recovery/guides');
    if (Array.isArray(res)) return res;
    return res?.guides || [];
  },

  getDeviceGuide: (deviceId: number) =>
    api.get<DeviceRecoveryContext>(`/recovery/guide/${deviceId}`),

  getRecoveryRecords: async (): Promise<RecoveryRecord[]> => {
    const res = await api.get<RecoveryRecord[] | { items: RecoveryRecord[] }>('/recovery/records');
    if (Array.isArray(res)) return res;
    return res?.items || [];
  },

  createRecoveryRecord: (payload: {
    device_id: number;
    manufacturer: string;
    model?: string;
    method_used: string;
    status: string;
    notes?: string;
  }) => api.post<RecoveryRecord>('/recovery/records', payload),

  saveVaultCredentials: (payload: SaveVaultCredentialsPayload) =>
    api.post<VaultStatus & { saved?: boolean; message?: string }>(
      '/recovery/vault/credentials',
      payload
    ),

  getVaultStatus: (deviceId: number) =>
    api.get<VaultStatus>(`/recovery/vault/status/${deviceId}`),

  deleteVaultCredentials: (deviceId: number) =>
    api.delete<{ deleted: boolean; message?: string }>(
      `/recovery/vault/credentials/${deviceId}`
    ),
};
