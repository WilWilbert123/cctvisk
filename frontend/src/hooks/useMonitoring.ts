import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { monitoringService } from '../services/monitoringService';

export function useMonitoringStatus() {
  return useQuery({
    queryKey: ['monitoring', 'status'],
    queryFn: () => monitoringService.getStatus(),
    refetchInterval: 4000,
  });
}

export function useStartMonitoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => monitoringService.startMonitoring(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring'] });
    },
  });
}

export function useStopMonitoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => monitoringService.stopMonitoring(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring'] });
    },
  });
}

export function useUpdateMonitoringConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: monitoringService.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring'] });
    },
  });
}

export function useCheckNowMonitoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => monitoringService.checkNow(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useHistoryData() {
  const scans = useQuery({
    queryKey: ['history', 'scans'],
    queryFn: () => monitoringService.getScanHistory(),
  });
  const devices = useQuery({
    queryKey: ['history', 'devices'],
    queryFn: () => monitoringService.getDeviceHistory(),
  });
  const recovery = useQuery({
    queryKey: ['history', 'recovery'],
    queryFn: () => monitoringService.getRecoveryHistory(),
  });
  const activity = useQuery({
    queryKey: ['history', 'activity'],
    queryFn: () => monitoringService.getActivityHistory(),
  });

  return { scans, devices, recovery, activity };
}

export function useAppSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => monitoringService.getSettings(),
  });
}
