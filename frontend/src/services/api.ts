import type { QueryClient } from '@tanstack/react-query';
import { useNetworkStore } from '../store/networkStore';

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const savedHost = window.localStorage.getItem('cctv_backend_host');
    if (savedHost && savedHost.trim()) {
      const clean = savedHost.trim().replace(/\/+$/, '');
      return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
    }
    if (window.location.protocol === 'file:' || Boolean((window as any).AndroidNativeScanner)) {
      return 'http://192.168.0.85:8000/api/v1';
    }
  }
  return import.meta.env.VITE_API_BASE_URL || '/api/v1';
}

export const API_BASE_URL = getApiBaseUrl();

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(message: string, status = 500, code = 'API_ERROR', details?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== 'undefined'
      ? window.localStorage.getItem('cctv_api_token')
      : null;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('X-API-Token', token);
  }

  const baseUrl = getApiBaseUrl();
  const normalizedEndpoint = endpoint.startsWith('http')
    ? endpoint
    : `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  let response: Response;
  try {
    response = await fetch(normalizedEndpoint, {
      ...options,
      headers,
    });
  } catch (networkErr) {
    // If running inside the standalone Android APK and the laptop backend is unreachable,
    // use the on-phone Native Android Java Network Discovery bridge!
    const androidBridge =
      typeof window !== 'undefined' ? (window as any).AndroidNativeScanner : null;
    if (androidBridge && typeof androidBridge.handleApiRequest === 'function') {
      const rawJson = androidBridge.handleApiRequest(
        options.method || 'GET',
        endpoint,
        typeof options.body === 'string' ? options.body : ''
      );
      const parsed = JSON.parse(rawJson);
      if (parsed && typeof parsed === 'object' && 'data' in parsed && 'success' in parsed) {
        return parsed.data as T;
      }
      return parsed as T;
    }
    throw networkErr;
  }

  let payload: any = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  } else {
    const text = await response.text();
    payload = text || null;
  }

  if (!response.ok || (payload && typeof payload === 'object' && payload.success === false)) {
    const errObj = payload?.error;
    const message =
      errObj?.message ||
      (typeof payload?.detail === 'string' ? payload.detail : null) ||
      payload?.message ||
      `Request failed with status ${response.status}`;
    const code = errObj?.code || `HTTP_${response.status}`;
    throw new ApiClientError(message, response.status, code, errObj?.details || payload);
  }

  if (payload && typeof payload === 'object' && 'data' in payload && 'success' in payload) {
    return payload.data as T;
  }

  return payload as T;
}

export const api = {
  get: <T>(endpoint: string, params?: Record<string, string | number | boolean | undefined | null>) => {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '' && value !== 'all') {
          searchParams.append(key, String(value));
        }
      });
      const qs = searchParams.toString();
      if (qs) {
        url += (url.includes('?') ? '&' : '?') + qs;
      }
    }
    return apiRequest<T>(url, { method: 'GET' });
  },
  post: <T>(endpoint: string, body?: unknown) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown) =>
    apiRequest<T>(endpoint, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string) =>
    apiRequest<T>(endpoint, {
      method: 'DELETE',
    }),
};

export function createRealtimeSocket(queryClient: QueryClient): () => void {
  if (typeof window === 'undefined' || typeof WebSocket === 'undefined') {
    return () => {};
  }

  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let isClosedIntentionally = false;

  const connect = () => {
    if (isClosedIntentionally) return;
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const token = window.localStorage.getItem('cctv_api_token') || '';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws${
        token ? `?token=${encodeURIComponent(token)}` : ''
      }`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        useNetworkStore.getState().setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const eventType = message.event || message.type;
          const data = message.data || message.payload || message;

          if (eventType === 'scan_progress') {
            useNetworkStore.getState().setScanStatus({
              is_running: data.is_running ?? (data.progress < 100 && data.stage !== 'completed'),
              progress: typeof data.progress === 'number' ? data.progress : 0,
              stage: data.stage || 'scanning',
              message: data.message || 'Scanning network...',
              devices_found: data.devices_found ?? 0,
              cameras_found: data.cameras_found ?? 0,
            });
            if (data.progress >= 100 || data.stage === 'completed' || data.is_running === false) {
              queryClient.invalidateQueries({ queryKey: ['dashboard'] });
              queryClient.invalidateQueries({ queryKey: ['devices'] });
              queryClient.invalidateQueries({ queryKey: ['cameras'] });
              queryClient.invalidateQueries({ queryKey: ['nvr'] });
              queryClient.invalidateQueries({ queryKey: ['scan-status'] });
              queryClient.invalidateQueries({ queryKey: ['history'] });
            }
          } else if (eventType === 'device_discovered') {
            queryClient.invalidateQueries({ queryKey: ['devices'] });
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
          } else if (eventType === 'device_status_changed' || eventType === 'monitoring_event') {
            queryClient.invalidateQueries({ queryKey: ['monitoring'] });
            queryClient.invalidateQueries({ queryKey: ['devices'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
          } else if (eventType === 'system_notification') {
            useNetworkStore.getState().addNotification({
              type: data.level || 'info',
              title: data.title || 'System Notification',
              message: data.message || '',
            });
          }
        } catch {
          // Ignore malformed WS packets
        }
      };

      ws.onclose = () => {
        useNetworkStore.getState().setWsConnected(false);
        if (!isClosedIntentionally) {
          reconnectTimer = setTimeout(connect, 5000);
        }
      };

      ws.onerror = () => {
        useNetworkStore.getState().setWsConnected(false);
      };
    } catch {
      if (!isClosedIntentionally) {
        reconnectTimer = setTimeout(connect, 5000);
      }
    }
  };

  connect();

  return () => {
    isClosedIntentionally = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) {
      ws.close();
    }
  };
}
