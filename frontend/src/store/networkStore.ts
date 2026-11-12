import { create } from 'zustand';
import type { NetworkInfoResponse, ScanStatusResponse } from '../types/network';

interface NotificationBanner {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
}

interface NetworkState {
  networkInfo: NetworkInfoResponse | null;
  scanStatus: ScanStatusResponse;
  wsConnected: boolean;
  authorizedScanConfirmed: boolean;
  selectedSubnet: string;
  selectedInterface: string;
  notifications: NotificationBanner[];
  setNetworkInfo: (info: NetworkInfoResponse | null) => void;
  setScanStatus: (status: Partial<ScanStatusResponse>) => void;
  setWsConnected: (connected: boolean) => void;
  setAuthorizedScanConfirmed: (confirmed: boolean) => void;
  setSelectedSubnet: (subnet: string) => void;
  setSelectedInterface: (iface: string) => void;
  addNotification: (notif: Omit<NotificationBanner, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useNetworkStore = create<NetworkState>((set) => ({
  networkInfo: null,
  scanStatus: {
    is_running: false,
    progress: 0,
    stage: 'idle',
    message: 'Ready to scan local network',
    devices_found: 0,
    cameras_found: 0,
    current_scan: null,
  },
  wsConnected: false,
  authorizedScanConfirmed: false,
  selectedSubnet: '',
  selectedInterface: '',
  notifications: [],
  setNetworkInfo: (info) =>
    set((state) => {
      const subnetChanged =
        info?.subnet_cidr && state.networkInfo?.subnet_cidr !== info.subnet_cidr;
      return {
        networkInfo: info,
        selectedSubnet:
          subnetChanged || !state.selectedSubnet
            ? info?.subnet_cidr || ''
            : state.selectedSubnet,
        selectedInterface:
          subnetChanged || !state.selectedInterface
            ? info?.interface_name || ''
            : state.selectedInterface,
      };
    }),
  setScanStatus: (status) =>
    set((state) => ({
      scanStatus: {
        ...state.scanStatus,
        ...status,
      },
    })),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setAuthorizedScanConfirmed: (confirmed) => set({ authorizedScanConfirmed: confirmed }),
  setSelectedSubnet: (subnet) => set({ selectedSubnet: subnet }),
  setSelectedInterface: (iface) => set({ selectedInterface: iface }),
  addNotification: (notif) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    set((state) => ({
      notifications: [
        {
          ...notif,
          id,
          timestamp: new Date().toISOString(),
        },
        ...state.notifications.filter((n) => n.message !== notif.message).slice(0, 1),
      ],
    }));
    if (typeof window !== 'undefined') {
      window.setTimeout(() => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      }, 4000);
    }
  },
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));
