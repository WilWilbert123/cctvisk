import { create } from 'zustand';
import type { Device } from '../types/device';
import type { Camera, CameraConnectResponse } from '../types/camera';

interface DeviceFilterState {
  search: string;
  category: string;
  isOnline: string; // 'all' | 'online' | 'offline'
  confidence: string; // 'all' | 'HIGH' | 'MEDIUM' | 'LOW'
  sortBy: string;
}

interface DeviceState {
  selectedDevice: Device | null;
  activeLiveCamera: Camera | null;
  liveConnections: Record<number, CameraConnectResponse>;
  multiGridActive: boolean;
  filters: DeviceFilterState;
  setSelectedDevice: (device: Device | null) => void;
  setActiveLiveCamera: (camera: Camera | null) => void;
  setLiveConnection: (cameraId: number, connection: CameraConnectResponse) => void;
  removeLiveConnection: (cameraId: number) => void;
  setMultiGridActive: (active: boolean) => void;
  setFilters: (filters: Partial<DeviceFilterState>) => void;
  resetFilters: () => void;
}

const initialFilters: DeviceFilterState = {
  search: '',
  category: 'all',
  isOnline: 'all',
  confidence: 'all',
  sortBy: 'ip_address',
};

export const useDeviceStore = create<DeviceState>((set) => ({
  selectedDevice: null,
  activeLiveCamera: null,
  liveConnections: {},
  multiGridActive: false,
  filters: initialFilters,
  setSelectedDevice: (device) => set({ selectedDevice: device }),
  setActiveLiveCamera: (camera) => set({ activeLiveCamera: camera }),
  setLiveConnection: (cameraId, connection) =>
    set((state) => ({
      liveConnections: {
        ...state.liveConnections,
        [cameraId]: connection,
      },
    })),
  removeLiveConnection: (cameraId) =>
    set((state) => {
      const next = { ...state.liveConnections };
      delete next[cameraId];
      return { liveConnections: next };
    }),
  setMultiGridActive: (active) => set({ multiGridActive: active }),
  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    })),
  resetFilters: () => set({ filters: initialFilters }),
}));
