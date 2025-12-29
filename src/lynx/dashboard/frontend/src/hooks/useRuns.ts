import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchRuns, fetchStrategies, deleteRun } from '../api/client'
import type { RunsQueryParams } from '../types/api'

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
