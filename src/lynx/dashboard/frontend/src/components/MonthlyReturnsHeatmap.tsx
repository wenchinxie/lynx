import { useMemo } from 'react'
import type { RunSummary, MonthlyReturnsResponse } from '../types/api'
import { useMonthlyReturns } from '../hooks/useRuns'

interface MonthlyReturnsHeatmapProps {
  runs: RunSummary[]
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function getReturnColor(value: number | undefined): string {
  if (value == null) return 'bg-[var(--color-bg-tertiary)]'
  if (value >= 0.1) return 'bg-emerald-600'
  if (value >= 0.05) return 'bg-emerald-500'
  if (value >= 0.02) return 'bg-emerald-400/70'
  if (value >= 0) return 'bg-emerald-300/50'
  if (value >= -0.02) return 'bg-red-300/50'
  if (value >= -0.05) return 'bg-red-400/70'
  if (value >= -0.1) return 'bg-red-500'
  return 'bg-red-600'
}

function formatPercent(value: number | undefined): string {
  if (value == null) return '-'
  const pct = (value * 100).toFixed(1)
  return value >= 0 ? `+${pct}%` : `${pct}%`
}

function calculateYearlyReturn(monthlyReturns: Record<number, number>): number {
  return Object.values(monthlyReturns).reduce((acc, val) => acc + val, 0)
}

// Group monthly returns by strategy
function groupByStrategy(
  monthlyReturnsData: MonthlyReturnsResponse[]
): Record<string, Record<number, Record<number, number>>> {
  const grouped: Record<string, Record<number, Record<number, number>>> = {}

  for (const data of monthlyReturnsData) {
    const strategyName = data.strategy_name
    if (!grouped[strategyName]) {
      grouped[strategyName] = {}
    }
    // Merge monthly returns (sum if same month)
    for (const [yearStr, months] of Object.entries(data.monthly_returns)) {
      const year = parseInt(yearStr, 10)
      if (!grouped[strategyName][year]) {
        grouped[strategyName][year] = {}
      }
      for (const [monthStr, ret] of Object.entries(months)) {
        const month = parseInt(monthStr, 10)
        grouped[strategyName][year][month] =
          (grouped[strategyName][year][month] || 0) + ret
      }
    }
  }

  return grouped
}

function StrategyHeatmap({
  strategyName,
  monthlyReturns,
  years,
}: {
  strategyName: string
  monthlyReturns: Record<number, Record<number, number>>
  years: number[]
}) {
  const validYears = years.filter((y) => monthlyReturns[y])

  if (validYears.length === 0) {
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          {strategyName}
        </h3>
        <p className="text-sm text-[var(--color-text-secondary)]">No monthly returns data available</p>
      </div>
    )
  }

  // Calculate summary stats
  const yearlyReturns = validYears.map((y) => ({
    year: y,
    ret: calculateYearlyReturn(monthlyReturns[y] || {}),
  }))

  const bestYear = yearlyReturns.length > 0
    ? yearlyReturns.reduce((a, b) => (a.ret > b.ret ? a : b))
    : null
  const worstYear = yearlyReturns.length > 0
    ? yearlyReturns.reduce((a, b) => (a.ret < b.ret ? a : b))
    : null
  const avgAnnual = yearlyReturns.length > 0
    ? yearlyReturns.reduce((acc, y) => acc + y.ret, 0) / yearlyReturns.length
    : 0

  return (
    <div className="mb-8 last:mb-0">
      <h3 className="text-lg font-semibold text-[var(--color-accent)] mb-4">
        {strategyName}
      </h3>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">Year</th>
              {MONTHS.map((month) => (
                <th key={month} className="py-2 px-1 text-center text-[var(--color-text-secondary)] font-medium">
                  {month}
                </th>
              ))}
              <th className="py-2 px-2 text-center text-[var(--color-text-secondary)] font-medium">YTD</th>
            </tr>
          </thead>
          <tbody>
            {validYears.map((year) => (
              <tr key={year}>
                <td className="py-1 px-2 text-[var(--color-text-primary)] font-medium">{year}</td>
                {MONTHS.map((_, monthIndex) => {
                  const value = monthlyReturns[year]?.[monthIndex + 1]
                  return (
                    <td key={monthIndex} className="py-1 px-1">
                      <div
                        className={`${getReturnColor(value)} rounded px-1 py-1 text-center text-xs font-medium text-white min-w-[48px]`}
                        title={formatPercent(value)}
                      >
                        {formatPercent(value)}
                      </div>
                    </td>
                  )
                })}
                <td className="py-1 px-2">
                  <div
                    className={`${getReturnColor(calculateYearlyReturn(monthlyReturns[year] || {}))} rounded px-2 py-1 text-center text-xs font-bold text-white`}
                  >
                    {formatPercent(calculateYearlyReturn(monthlyReturns[year] || {}))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4">
          <div className="text-sm text-[var(--color-text-secondary)]">Best Year</div>
          <div className="text-xl font-bold text-[var(--color-positive)] mt-1">
            {bestYear ? `${bestYear.year}: ${formatPercent(bestYear.ret)}` : '-'}
          </div>
        </div>
        <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4">
          <div className="text-sm text-[var(--color-text-secondary)]">Worst Year</div>
          <div className="text-xl font-bold text-[var(--color-negative)] mt-1">
            {worstYear ? `${worstYear.year}: ${formatPercent(worstYear.ret)}` : '-'}
          </div>
        </div>
        <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4">
          <div className="text-sm text-[var(--color-text-secondary)]">Avg Annual Return</div>
          <div className="text-xl font-bold text-[var(--color-accent)] mt-1">
            {formatPercent(avgAnnual)}
          </div>
        </div>
      </div>
    </div>
  )
}

export function MonthlyReturnsHeatmap({ runs }: MonthlyReturnsHeatmapProps) {
  const runIds = useMemo(() => runs.map((r) => r.id), [runs])
  const { data: monthlyReturnsData, isLoading } = useMonthlyReturns(runIds)

  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 10 }, (_, i) => currentYear - 9 + i)

  // Group by strategy
  const strategyData = useMemo(
    () => groupByStrategy(monthlyReturnsData),
    [monthlyReturnsData]
  )

  const strategyNames = Object.keys(strategyData).sort()

  if (runs.length === 0) {
    return (
      <div className="bg-[var(--color-bg-secondary)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
          Monthly Returns
        </h2>
        <p className="text-[var(--color-text-secondary)]">No runs available</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-[var(--color-bg-secondary)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
          Monthly Returns
        </h2>
        <p className="text-[var(--color-text-secondary)]">Loading...</p>
      </div>
    )
  }

  if (strategyNames.length === 0) {
    return (
      <div className="bg-[var(--color-bg-secondary)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
          Monthly Returns
        </h2>
        <p className="text-[var(--color-text-secondary)]">No monthly returns data available</p>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg-secondary)] rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
        Monthly Returns by Strategy
      </h2>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-6 text-sm text-[var(--color-text-secondary)]">
        <span>Returns:</span>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-red-600" />
          <span>&lt;-10%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-red-400/70" />
          <span>-5%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-emerald-300/50" />
          <span>0%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-emerald-500" />
          <span>+5%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-emerald-600" />
          <span>&gt;+10%</span>
        </div>
      </div>

      {/* Strategy Heatmaps */}
      {strategyNames.map((strategyName) => (
        <StrategyHeatmap
          key={strategyName}
          strategyName={strategyName}
          monthlyReturns={strategyData[strategyName]}
          years={years}
        />
      ))}
    </div>
  )
}
