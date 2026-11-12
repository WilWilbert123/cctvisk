import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { discoveryService } from '../services/discoveryService';

export function useDiscoveryResults() {
  return useQuery({
    queryKey: ['discovery', 'results'],
    queryFn: () => discoveryService.getResults(),
  });
}

export function useRunDiscoveryProbe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (methods: string[]) => discoveryService.runProbe(methods),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
    },
  });
}

export function useCommonPorts() {
  return useQuery({
    queryKey: ['ports', 'common'],
    queryFn: () => discoveryService.getCommonPorts(),
  });
}

export function usePortScan() {
  return useMutation({
    mutationFn: ({ ip_address, ports }: { ip_address: string; ports?: number[] }) =>
      discoveryService.scanPorts(ip_address, ports),
  });
}

export function useOnvifDiscover() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => discoveryService.discoverOnvif(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
    },
  });
}

export function useOnvifInterrogate() {
  return useMutation({
    mutationFn: discoveryService.interrogateOnvif,
  });
}
