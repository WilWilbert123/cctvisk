import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cameraService } from '../services/cameraService';
import { useDeviceStore } from '../store/deviceStore';
import { useNetworkStore } from '../store/networkStore';
import type { CameraConnectRequest, CreateCameraPayload, Camera } from '../types/camera';

export function useCameras() {
  return useQuery({
    queryKey: ['cameras'],
    queryFn: () => cameraService.getCameras(),
    refetchInterval: 4000,
  });
}

export function useCameraDetail(id: number | null) {
  return useQuery({
    queryKey: ['cameras', 'detail', id],
    queryFn: () => cameraService.getCameraById(id as number),
    enabled: typeof id === 'number' && id > 0,
  });
}

export function useCreateCamera() {
  const queryClient = useQueryClient();
  const addNotification = useNetworkStore((s) => s.addNotification);

  return useMutation({
    mutationFn: (payload: CreateCameraPayload) => cameraService.createCamera(payload),
    onSuccess: (camera) => {
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addNotification({
        type: 'success',
        title: 'Camera Added',
        message: `${camera.label || camera.ip_address} added to CCTV inventory`,
      });
    },
  });
}

export function useUpdateCamera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Camera> }) =>
      cameraService.updateCamera(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });
}

export function useDeleteCamera() {
  const queryClient = useQueryClient();
  const addNotification = useNetworkStore((s) => s.addNotification);
  const removeLiveConnection = useDeviceStore((s) => s.removeLiveConnection);

  return useMutation({
    mutationFn: (id: number) => cameraService.deleteCamera(id),
    onSuccess: (_, id) => {
      removeLiveConnection(id);
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addNotification({
        type: 'info',
        title: 'Camera Removed',
        message: 'Removed entry from CCTV Cameras matrix',
      });
    },
  });
}

export function useConnectCamera() {
  const queryClient = useQueryClient();
  const setLiveConnection = useDeviceStore((s) => s.setLiveConnection);

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CameraConnectRequest }) =>
      cameraService.connectCamera(id, payload),
    onSuccess: (res, variables) => {
      setLiveConnection(variables.id, res);
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
    },
  });
}

export function useCameraStreamStatus(id: number | null, enabled = false) {
  return useQuery({
    queryKey: ['cameras', 'stream-status', id],
    queryFn: () => cameraService.getStreamStatus(id as number),
    enabled: Boolean(id && enabled),
    refetchInterval: 3000,
  });
}

export function useStopCameraStream() {
  const removeLiveConnection = useDeviceStore((s) => s.removeLiveConnection);
  return useMutation({
    mutationFn: (id: number) => cameraService.stopStream(id),
    onSuccess: (_, id) => {
      removeLiveConnection(id);
    },
  });
}
