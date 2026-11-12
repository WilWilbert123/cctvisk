import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { networkService } from '../services/networkService';
import { useNetworkStore } from '../store/networkStore';
import type { ScanStartRequest } from '../types/network';

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => networkService.getDashboardSummary(),
    refetchInterval: 4000,
  });
}

export function useNetworkInfo() {
  const setNetworkInfo = useNetworkStore((s) => s.setNetworkInfo);
  const query = useQuery({
    queryKey: ['network', 'info'],
    queryFn: () => networkService.getNetworkInfo(),
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (query.data) {
      setNetworkInfo(query.data);
    }
  }, [query.data, setNetworkInfo]);

  return query;
}

export function useNetworkInterfaces() {
  return useQuery({
    queryKey: ['network', 'interfaces'],
    queryFn: () => networkService.getInterfaces(),
  });
}

export function useScanStatus() {
  const setScanStatus = useNetworkStore((s) => s.setScanStatus);
  const query = useQuery({
    queryKey: ['scan-status'],
    queryFn: () => networkService.getScanStatus(),
    refetchInterval: (queryState) =>
      queryState.state.data?.is_running ? 1500 : 8000,
  });

  useEffect(() => {
    if (query.data) {
      setScanStatus(query.data);
    }
  }, [query.data, setScanStatus]);

  return query;
}

export function useStartScan() {
  const queryClient = useQueryClient();
  const setScanStatus = useNetworkStore((s) => s.setScanStatus);
  const addNotification = useNetworkStore((s) => s.addNotification);

  return useMutation({
    mutationFn: (payload: ScanStartRequest) => networkService.startScan(payload),
    onSuccess: (scan) => {
      setScanStatus({
        is_running: true,
        progress: scan.progress || 5,
        stage: scan.stage || 'initializing',
        message: `Scanning subnet ${scan.subnet_cidr}...`,
        current_scan: scan,
      });
      queryClient.invalidateQueries({ queryKey: ['scan-status'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addNotification({
        type: 'info',
        title: 'Network Scan Started',
        message: `Active discovery started on ${scan.subnet_cidr}`,
      });
    },
    onError: (err: Error) => {
      addNotification({
        type: 'error',
        title: 'Scan Failed to Start',
        message: err.message,
      });
    },
  });
}

export function useCancelScan() {
  const queryClient = useQueryClient();
  const setScanStatus = useNetworkStore((s) => s.setScanStatus);

  return useMutation({
    mutationFn: () => networkService.cancelScan(),
    onSuccess: () => {
      setScanStatus({
        is_running: false,
        stage: 'cancelled',
        message: 'Scan cancelled by user',
      });
      queryClient.invalidateQueries({ queryKey: ['scan-status'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
    },
  });
}

export function useValidateSubnet() {
  return useMutation({
    mutationFn: (subnet_cidr: string) => networkService.validateSubnet(subnet_cidr),
  });
}
