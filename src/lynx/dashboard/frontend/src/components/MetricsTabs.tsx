import { useState } from 'react'
import type { CategorizedMetrics, MetricCategory } from '../types/api'
import { MetricsGrid } from './MetricsGrid'

interface MetricsTabsProps {
  data: CategorizedMetrics
}

const categoryLabels: Record<MetricCategory, string> = {
  profitability: 'Profitability',
  risk: 'Risk',
  ratio: 'Ratio',
  winrate: 'Win Rate',
  liquidity: 'Liquidity',
  backtest: 'Backtest',
}

export function MetricsTabs({ data }: MetricsTabsProps) {
  const [activeTab, setActiveTab] = useState<MetricCategory>(data.default_tab)

  const { metrics_by_category, category_order } = data

  return (
    <div className="bg-[var(--color-bg-primary)] rounded-lg p-4">
      <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
        Metrics
      </h4>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-[var(--color-border)]">
        {category_order.map((category) => {
          const catData = metrics_by_category[category]
          if (!catData || catData.metrics.length === 0) return null

          const { summary } = catData
          const isActive = category === activeTab

          return (
            <button
              key={category}
              onClick={() => setActiveTab(category)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-[var(--color-accent)] text-white'
                  : 'border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]'
              }`}
            >
              {categoryLabels[category]}
              <span className="flex gap-1 text-xs">
                {summary.green > 0 && (
                  <span className="px-1.5 py-0.5 rounded bg-[var(--color-positive)]/20 text-[var(--color-positive)]">
                    {summary.green}
                  </span>
                )}
                {summary.yellow > 0 && (
                  <span className="px-1.5 py-0.5 rounded bg-[var(--color-warning)]/20 text-[var(--color-warning)]">
                    {summary.yellow}
                  </span>
                )}
                {summary.red > 0 && (
                  <span className="px-1.5 py-0.5 rounded bg-[var(--color-negative)]/20 text-[var(--color-negative)]">
                    {summary.red}
                  </span>
                )}
              </span>
            </button>
          )
        })}
      </div>

      {/* Active Tab Content */}
      {category_order.map((category) => {
        const catData = metrics_by_category[category]
        if (!catData || category !== activeTab) return null

        return <MetricsGrid key={category} metrics={catData.metrics} />
      })}
    </div>
  )
}
