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

  const sharpes = runs
    .map((r) => r.metrics?.sharpe_ratio)
    .filter((v): v is number => v != null)
  const returns = runs
    .map((r) => r.metrics?.total_return)
    .filter((v): v is number => v != null)

  const bestSharpe = sharpes.length > 0 ? Math.max(...sharpes) : null
  const bestReturn = returns.length > 0 ? Math.max(...returns) : null

  const stats = [
    { label: 'Total Runs', value: runs.length.toString() },
    { label: 'Strategies', value: strategies.size.toString() },
    { label: 'Best Sharpe', value: formatNumber(bestSharpe ?? undefined) },
    { label: 'Best Return', value: formatPercent(bestReturn ?? undefined) },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
