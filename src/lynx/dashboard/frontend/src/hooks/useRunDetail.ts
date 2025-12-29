import { useQuery } from '@tanstack/react-query'
import { fetchRunDetail, fetchRunMetrics, fetchRunTrades } from '../api/client'

export function useRunDetail(runId: string | null) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => fetchRunDetail(runId!),
    enabled: !!runId,
  })
}

export function useRunMetrics(runId: string | null) {
  return useQuery({
    queryKey: ['runMetrics', runId],
    queryFn: () => fetchRunMetrics(runId!),
    enabled: !!runId,
  })
}

export function useRunTrades(runId: string | null, page: number = 1, pageSize: number = 100) {
  return useQuery({
    queryKey: ['runTrades', runId, page, pageSize],
    queryFn: () => fetchRunTrades(runId!, page, pageSize),
    enabled: !!runId,
  })
}
