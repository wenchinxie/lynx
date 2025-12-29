import type { FormattedMetric, HealthStatus } from '../types/api'

interface MetricsGridProps {
  metrics: FormattedMetric[]
}

function HealthDot({ health }: { health: HealthStatus }) {
  if (!health) return null

  const colors = {
    green: 'bg-[var(--color-positive)]',
    yellow: 'bg-[var(--color-warning)]',
    red: 'bg-[var(--color-negative)]',
  }

  return <span className={`inline-block w-2 h-2 rounded-full ml-2 ${colors[health]}`} />
}

function MetricCard({ metric }: { metric: FormattedMetric }) {
  const borderColors = {
    green: 'border-l-[var(--color-positive)]',
    yellow: 'border-l-[var(--color-warning)]',
    red: 'border-l-[var(--color-negative)]',
  }

  const borderClass = metric.health
    ? borderColors[metric.health]
    : 'border-l-[var(--color-border)]'

  return (
    <div
      className={`bg-[var(--color-bg-primary)] p-4 rounded-lg border-l-4 ${borderClass} hover:-translate-y-0.5 transition-transform`}
    >
      <div className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide mb-1">
        {metric.label}
      </div>
      <div
        className={`text-lg font-semibold ${
          metric.is_special
            ? 'text-[var(--color-text-secondary)] italic'
            : metric.is_negative
            ? 'text-[var(--color-negative)]'
            : 'text-[var(--color-text-primary)]'
        }`}
      >
        {metric.formatted}
        <HealthDot health={metric.health} />
      </div>
    </div>
  )
}

export function MetricsGrid({ metrics }: MetricsGridProps) {
  return (
    <div className="grid grid-cols-5 gap-4">
      {metrics.map((metric) => (
        <MetricCard key={metric.key} metric={metric} />
      ))}
    </div>
  )
}
