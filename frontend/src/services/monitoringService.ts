import { api } from './api';
import type { MonitoringStatusResponse } from '../types/device';

export const monitoringService = {
  getStatus: () => api.get<MonitoringStatusResponse>('/monitoring/status'),

  startMonitoring: () =>
    api.post<{ is_running: boolean; message?: string }>('/monitoring/start'),

  stopMonitoring: () =>
    api.post<{ is_running: boolean; message?: string }>('/monitoring/stop'),

  updateConfig: (payload: {
    interval_seconds: number;
    timeout_ms?: number;
    alert_on_offline?: boolean;
  }) => api.patch<MonitoringStatusResponse>('/monitoring/config', payload),

  checkNow: () =>
    api.post<{ checked_count: number; online_count: number; offline_count: number; message?: string }>(
      '/monitoring/check-now'
    ),

  getScanHistory: async () => {
    const res = await api.get<any>('/history/scans');
    return Array.isArray(res) ? res : res?.items || [];
  },

  getDeviceHistory: async () => {
    const res = await api.get<any>('/history/devices');
    return Array.isArray(res) ? res : res?.items || [];
  },

  getRecoveryHistory: async () => {
    const res = await api.get<any>('/history/recovery');
    return Array.isArray(res) ? res : res?.items || [];
  },

  getActivityHistory: async () => {
    const res = await api.get<any>('/history/activity');
    return Array.isArray(res) ? res : res?.items || [];
  },

  getSettings: () =>
    api.get<{
      settings: Record<string, any>;
      vault_status: {
        initialized: boolean;
        encrypted_entries_count: number;
        algorithm: string;
      };
      database_health: {
        status: string;
        size_bytes?: number;
        path?: string;
        tables_count?: number;
      };
      lan_access: {
        enabled: boolean;
        bind_host: string;
        port: number;
        pairing_token_required?: boolean;
        local_urls?: string[];
      };
    }>('/settings'),

  updateSettings: (category: string, values: Record<string, any>) =>
    api.patch<{ updated: boolean; settings: Record<string, any> }>('/settings', {
      category,
      values,
    }),

  createBackup: () =>
    api.post<{ backup_path: string; timestamp: string; size_bytes?: number; message?: string }>(
      '/settings/backup'
    ),

  exportInventory: () =>
    api.post<{ exported_at: string; total_devices: number; devices: any[] }>('/settings/export'),

  getSystemHealth: () =>
    api.get<{ status: string; version: string; uptime_seconds?: number }>('/system/health'),

  getSystemDiagnostics: () => api.get<Record<string, any>>('/system/diagnostics'),

  pairWithToken: (token: string) =>
    api.post<{ paired: boolean; message?: string }>('/system/pair', { token }),
};
