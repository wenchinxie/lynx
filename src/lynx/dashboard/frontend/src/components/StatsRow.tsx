import type { RunSummary } from '../types/api'

interface StatsRowProps {
  runs: RunSummary[]
}

function formatPercent(value: number | undefined): string {
  if (value == null) return '-'
  const pct = (value * 100).toFixed(2)
  return value >= 0 ? `+${pct}%` : `${pct}%`
}

function formatNumber(value: number | undefined, decimals = 2): string {
  if (value == null) return '-'
  return value.toFixed(decimals)
}

export function StatsRow({ runs }: StatsRowProps) {
  const strategies = new Set(runs.map((r) => r.strategy_name))

  // Helper to get metric value (supports both camelCase and snake_case)
  const getMetric = (metrics: Record<string, unknown> | undefined, ...keys: string[]): number | undefined => {
    if (!metrics) return undefined
    for (const key of keys) {
      const val = metrics[key]
      if (typeof val === 'number' && isFinite(val)) return val
    }
    return undefined
  }

  const sharpes = runs
    .map((r) => getMetric(r.metrics, 'sharpeRatio', 'sharpe_ratio'))
    .filter((v): v is number => v != null)
  const returns = runs
    .map((r) => getMetric(r.metrics, 'annualReturn', 'total_return', 'annualized_return'))
    .filter((v): v is number => v != null)

  const bestSharpe = sharpes.length > 0 ? Math.max(...sharpes) : null
  const bestReturn = returns.length > 0 ? Math.max(...returns) : null

  // Avg Return
  const avgReturn = returns.length > 0
    ? returns.reduce((a, b) => a + b, 0) / returns.length
    : null

  // Avg Sharpe
  const avgSharpe = sharpes.length > 0
    ? sharpes.reduce((a, b) => a + b, 0) / sharpes.length
    : null

  // Worst Drawdown
  const drawdowns = runs
    .map((r) => getMetric(r.metrics, 'maxDrawdown', 'max_drawdown'))
    .filter((v): v is number => v != null)
  const worstDrawdown = drawdowns.length > 0 ? Math.min(...drawdowns) : null

  // Total Trades (from trades artifact, not metrics - use winRate count as proxy)
  const winRates = runs
    .map((r) => getMetric(r.metrics, 'winRate', 'win_rate'))
    .filter((v): v is number => v != null)
  const avgWinRate = winRates.length > 0
    ? winRates.reduce((a, b) => a + b, 0) / winRates.length
    : null

  const stats = [
    { label: 'Total Runs', value: runs.length.toString() },
    { label: 'Strategies', value: strategies.size.toString() },
    { label: 'Best Sharpe', value: formatNumber(bestSharpe ?? undefined) },
    { label: 'Best Return', value: formatPercent(bestReturn ?? undefined) },
    { label: 'Avg Return', value: formatPercent(avgReturn ?? undefined) },
    { label: 'Avg Sharpe', value: formatNumber(avgSharpe ?? undefined) },
    { label: 'Worst Drawdown', value: formatPercent(worstDrawdown ?? undefined) },
    { label: 'Avg Win Rate', value: formatPercent(avgWinRate ?? undefined) },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-[var(--color-bg-secondary)] p-4 rounded-lg text-center"
        >
          <div className="text-2xl font-bold text-[var(--color-accent)]">
            {stat.value}
          </div>
          <div className="text-sm text-[var(--color-text-secondary)] mt-1">
            {stat.label}
          </div>
        </div>
      ))}
    </div>
  )
}
