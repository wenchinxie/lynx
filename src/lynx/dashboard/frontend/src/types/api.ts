// Run types
export interface RunMetrics {
  total_return?: number
  annualized_return?: number
  sharpe_ratio?: number
  max_drawdown?: number
  win_rate?: number
  profit_factor?: number
  num_trades?: number
  avg_trade_duration_days?: number
  [key: string]: number | string | undefined
}

export interface RunSummary {
  id: string
  strategy_name: string
  created_at: string
  updated_at: string
  updated_at_relative?: string
  params: Record<string, unknown>
  metrics: RunMetrics
  tags?: string[]
}

export interface RunDetail extends RunSummary {
  artifacts: string[]
}

// Metrics types
export type HealthStatus = 'green' | 'yellow' | 'red' | null

export interface FormattedMetric {
  key: string
  label: string
  raw: number | string | null
  formatted: string
  health: HealthStatus
  is_negative: boolean
  is_special: boolean
}

export interface CategoryData {
  metrics: FormattedMetric[]
  summary: {
    green: number
    yellow: number
    red: number
  }
}

export type MetricCategory = 'profitability' | 'risk' | 'ratio' | 'winrate' | 'liquidity' | 'backtest'

export interface CategorizedMetrics {
  run_id: string
  metrics_by_category: Record<MetricCategory, CategoryData>
  category_order: MetricCategory[]
  default_tab: MetricCategory
}

// Trades types
export interface Trade {
  index: number
  symbol: string
  entry_date: string
  exit_date: string
  entry_price: number
  exit_price: number
  return: number
  [key: string]: unknown
}

export interface PaginatedResponse<T> {
  data: T[]
  total_rows: number
  page: number
  page_size: number
  total_pages: number
}

// Monthly returns
export interface MonthlyReturnsResponse {
  run_id: string
  strategy_name: string
  monthly_returns: Record<number, Record<number, number>>
}

// API query params
export interface RunsQueryParams {
  strategy?: string
  sort_by?: string
  order?: 'asc' | 'desc'
  limit?: number
}

// Strategy summary
export interface StrategySummary {
  strategy_name: string
  run_count: number
  last_updated: string
  last_updated_relative: string
  metrics: {
    best_return: number | null
    avg_return: number | null
    avg_sharpe: number | null
    best_sharpe: number | null
    worst_drawdown: number | null
  }
}
