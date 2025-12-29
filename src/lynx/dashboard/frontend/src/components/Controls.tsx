interface ControlsProps {
  strategies: string[]
  selectedStrategy: string
  onStrategyChange: (strategy: string) => void
  sortBy: string
  onSortChange: (sort: string) => void
  pollInterval: number
  onPollIntervalChange: (interval: number) => void
}

export function Controls({
  strategies,
  selectedStrategy,
  onStrategyChange,
  sortBy,
  onSortChange,
  pollInterval,
  onPollIntervalChange,
}: ControlsProps) {
  const selectClass =
    'bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-[var(--color-text-primary)] px-4 py-2 rounded-md text-sm focus:outline-none focus:border-[var(--color-accent)]'

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      <select
        value={selectedStrategy}
        onChange={(e) => onStrategyChange(e.target.value)}
        className={selectClass}
      >
        <option value="">All Strategies</option>
        {strategies.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      <select
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        className={selectClass}
      >
        <option value="created_at">Sort by Date</option>
        <option value="sharpe_ratio">Sort by Sharpe</option>
        <option value="total_return">Sort by Return</option>
        <option value="max_drawdown">Sort by Drawdown</option>
      </select>

      <select
        value={pollInterval}
        onChange={(e) => onPollIntervalChange(Number(e.target.value))}
        className={selectClass}
      >
        <option value={3000}>Refresh: 3s</option>
        <option value={5000}>Refresh: 5s</option>
        <option value={10000}>Refresh: 10s</option>
        <option value={0}>Manual only</option>
      </select>
    </div>
  )
}
