import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../api/client';

interface HealthResponse {
  service: string;
  status: string;
}

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: () => fetcher('/api/health'),
    staleTime: 60_000,
    retry: false,
  });
}
