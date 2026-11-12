import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  deviceService,
  type DeviceQueryParams,
  type CreateDevicePayload,
  type UpdateDevicePayload,
} from '../services/deviceService';
import { useNetworkStore } from '../store/networkStore';

export function useDevices(params: DeviceQueryParams = {}) {
  return useQuery({
    queryKey: ['devices', params],
    queryFn: () => deviceService.getDevices(params),
    refetchInterval: 4000,
  });
}

export function useDeviceDetail(id: number | null) {
  return useQuery({
    queryKey: ['devices', 'detail', id],
    queryFn: () => deviceService.getDeviceById(id as number),
    enabled: typeof id === 'number' && id > 0,
  });
}

export function useCreateDevice() {
  const queryClient = useQueryClient();
  const addNotification = useNetworkStore((s) => s.addNotification);

  return useMutation({
    mutationFn: (payload: CreateDevicePayload) => deviceService.createDevice(payload),
    onSuccess: (device) => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      queryClient.invalidateQueries({ queryKey: ['nvr'] });
      addNotification({
        type: 'success',
        title: 'Device Registered',
        message: `Added ${device.label || device.ip_address} to inventory`,
      });
    },
  });
}

export function useUpdateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateDevicePayload }) =>
      deviceService.updateDevice(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['monitoring'] });
    },
  });
}

export function useDeleteDevice() {
  const queryClient = useQueryClient();
  const addNotification = useNetworkStore((s) => s.addNotification);

  return useMutation({
    mutationFn: (id: number) => deviceService.deleteDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      queryClient.invalidateQueries({ queryKey: ['nvr'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addNotification({
        type: 'info',
        title: 'Device Removed',
        message: 'Device removed from inventory',
      });
    },
  });
}

export function useNVRDevices() {
  return useQuery({
    queryKey: ['nvr'],
    queryFn: () => deviceService.getNVRDevices(),
  });
}

export function useCreateNVR() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deviceService.createNVR,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nvr'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useDetectNVRChannels() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload?: { username?: string; password?: string; rtsp_port?: number; onvif_port?: number };
    }) => deviceService.detectNVRChannels(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nvr'] });
    },
  });
}
