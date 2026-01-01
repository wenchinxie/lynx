import type { MonthlyReturnsResponse } from '../types/api'

interface SingleRunHeatmapProps {
  data: MonthlyReturnsResponse | null | undefined
  isLoading: boolean
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

export function SingleRunHeatmap({ data, isLoading }: SingleRunHeatmapProps) {
  if (isLoading) {
    return (
      <div className="bg-[var(--color-bg-primary)] rounded-lg p-4">
        <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
          Monthly Returns
        </h4>
        <p className="text-[var(--color-text-muted)]">Loading...</p>
      </div>
    )
  }

  if (!data || Object.keys(data.monthly_returns).length === 0) {
    return (
      <div className="bg-[var(--color-bg-primary)] rounded-lg p-4">
        <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
          Monthly Returns
        </h4>
        <p className="text-[var(--color-text-muted)]">No monthly returns data available</p>
      </div>
    )
  }

  const monthlyReturns = data.monthly_returns
  const years = Object.keys(monthlyReturns)
    .map((y) => parseInt(y, 10))
    .sort((a, b) => a - b)

  return (
    <div className="bg-[var(--color-bg-primary)] rounded-lg p-4">
      <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
        Monthly Returns
      </h4>

      {/* Legend */}
      <div className="flex items-center gap-3 mb-4 text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-red-600" />
          <span>&lt;-10%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-emerald-300/50" />
          <span>0%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-emerald-600" />
          <span>&gt;+10%</span>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">Year</th>
              {MONTHS.map((month) => (
                <th key={month} className="py-2 px-1 text-center text-[var(--color-text-secondary)] font-medium text-xs">
                  {month}
                </th>
              ))}
              <th className="py-2 px-2 text-center text-[var(--color-text-secondary)] font-medium">YTD</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year}>
                <td className="py-1 px-2 text-[var(--color-text-primary)] font-medium">{year}</td>
                {MONTHS.map((_, monthIndex) => {
                  const value = monthlyReturns[year]?.[monthIndex + 1]
                  return (
                    <td key={monthIndex} className="py-1 px-0.5">
                      <div
                        className={`${getReturnColor(value)} rounded px-0.5 py-1 text-center text-xs font-medium text-white min-w-[40px]`}
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
    </div>
  )
}
