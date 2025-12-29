import type {
  RunSummary,
  RunDetail,
  CategorizedMetrics,
  Trade,
  PaginatedResponse,
  RunsQueryParams,
} from '../types/api'

const API_BASE = '/api'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

// Runs
export async function fetchRuns(params: RunsQueryParams = {}): Promise<RunSummary[]> {
  const searchParams = new URLSearchParams()
  if (params.strategy) searchParams.append('strategy', params.strategy)
  if (params.sort_by) searchParams.append('sort_by', params.sort_by)
  if (params.order) searchParams.append('order', params.order)
  if (params.limit) searchParams.append('limit', params.limit.toString())

  const query = searchParams.toString()
  return fetchJSON(`${API_BASE}/runs${query ? `?${query}` : ''}`)
}

export async function fetchRunDetail(runId: string): Promise<RunDetail> {
  return fetchJSON(`${API_BASE}/runs/${runId}`)
}

export async function fetchRunMetrics(runId: string): Promise<CategorizedMetrics> {
  return fetchJSON(`${API_BASE}/runs/${runId}/metrics`)
}

export async function fetchRunTrades(
  runId: string,
  page: number = 1,
  pageSize: number = 100
): Promise<PaginatedResponse<Trade>> {
  return fetchJSON(`${API_BASE}/runs/${runId}/trades?page=${page}&page_size=${pageSize}`)
}

export async function deleteRun(runId: string): Promise<void> {
  await fetch(`${API_BASE}/runs/${runId}`, { method: 'DELETE' })
}

// Strategies
export async function fetchStrategies(): Promise<string[]> {
  return fetchJSON(`${API_BASE}/strategies`)
}
