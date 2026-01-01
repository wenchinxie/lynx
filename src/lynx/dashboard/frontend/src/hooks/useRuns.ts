import { useQuery, useMutation, useQueryClient, useQueries } from '@tanstack/react-query'
import { fetchRuns, fetchStrategies, fetchStrategySummaries, deleteRun, fetchMonthlyReturns } from '../api/client'
import type { RunsQueryParams, MonthlyReturnsResponse } from '../types/api'

export function useRuns(params: RunsQueryParams = {}, refetchInterval: number = 5000) {
  return useQuery({
    queryKey: ['runs', params],
    queryFn: () => fetchRuns(params),
    refetchInterval: refetchInterval > 0 ? refetchInterval : false,
  })
}

export function useStrategies() {
  return useQuery({
    queryKey: ['strategies'],
    queryFn: fetchStrategies,
  })
}

export function useStrategySummaries(refetchInterval: number = 5000) {
  return useQuery({
    queryKey: ['strategies-summary'],
    queryFn: fetchStrategySummaries,
    refetchInterval: refetchInterval > 0 ? refetchInterval : false,
  })
}

export function useDeleteRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
    },
  })
}

export function useMonthlyReturns(runIds: string[]) {
  return useQueries({
    queries: runIds.map((runId) => ({
      queryKey: ['monthly-returns', runId],
      queryFn: () => fetchMonthlyReturns(runId),
      staleTime: 60000,
    })),
    combine: (results) => ({
      data: results
        .filter((r) => r.data)
        .map((r) => r.data as MonthlyReturnsResponse),
      isLoading: results.some((r) => r.isLoading),
      isError: results.some((r) => r.isError),
    }),
  })
}
