import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { RunSummary } from '../types/api'

interface ScatterPlotProps {
  runs: RunSummary[]
  onSelectRun: (runId: string) => void
}

interface DataPoint {
  id: string
  sharpe: number
  return: number
  label: string
}

function formatPercent(value: number): string {
  const pct = (value * 100).toFixed(2)
  return value >= 0 ? `+${pct}%` : `${pct}%`
}

export function ScatterPlot({ runs, onSelectRun }: ScatterPlotProps) {
  // Filter runs with valid sharpe and return
  const data: DataPoint[] = runs
    .filter((run) => run.metrics?.sharpe_ratio != null && run.metrics?.total_return != null)
    .map((run) => ({
      id: run.id,
      sharpe: run.metrics.sharpe_ratio!,
      return: run.metrics.total_return! * 100, // Convert to percentage
      label: run.id.slice(0, 8),
    }))

  if (data.length === 0) {
    return null
  }

  // Find best run (highest return with positive sharpe)
  const bestRunId = data.reduce((best, current) => {
    if (current.sharpe > 0 && current.return > (best?.return ?? -Infinity)) {
      return current
    }
    return best
  }, data[0])?.id

  return (
    <div className="bg-[var(--color-bg-secondary)] rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        Sharpe vs Return
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis
              type="number"
              dataKey="sharpe"
              name="Sharpe Ratio"
              tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickLine={{ stroke: 'var(--color-border)' }}
              label={{
                value: 'Sharpe Ratio',
                position: 'bottom',
                fill: 'var(--color-text-muted)',
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="return"
              name="Return"
              tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickLine={{ stroke: 'var(--color-border)' }}
              tickFormatter={(value) => `${value.toFixed(0)}%`}
              label={{
                value: 'Return (%)',
                angle: -90,
                position: 'insideLeft',
                fill: 'var(--color-text-muted)',
                fontSize: 12,
              }}
            />
            <Tooltip
              content={({ payload }) => {
                if (!payload || payload.length === 0) return null
                const point = payload[0].payload as DataPoint
                return (
                  <div className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded px-3 py-2 shadow-lg">
                    <div className="text-[var(--color-text-primary)] font-mono text-sm mb-1">
                      {point.id}
                    </div>
                    <div className="text-[var(--color-text-secondary)] text-sm">
                      Sharpe: {point.sharpe.toFixed(2)}
                    </div>
                    <div className="text-[var(--color-text-secondary)] text-sm">
                      Return: {formatPercent(point.return / 100)}
                    </div>
                  </div>
                )
              }}
            />
            <Scatter
              data={data}
              cursor="pointer"
              onClick={(data) => {
                if (data && data.id) {
                  onSelectRun(data.id)
                }
              }}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.id}
                  fill={entry.id === bestRunId ? 'var(--color-accent)' : 'var(--color-text-muted)'}
                  fillOpacity={entry.id === bestRunId ? 1 : 0.6}
                  r={entry.id === bestRunId ? 8 : 6}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[var(--color-text-muted)] text-xs mt-2 text-center">
        Click a point to view run details. Highlighted point has best return with positive Sharpe.
      </p>
    </div>
  )
}
