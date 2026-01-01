import { useState } from 'react'
import { useRuns, useDeleteRun } from '../hooks/useRuns'
import { RunsTable } from '../components/RunsTable'
import { RunDetailModal } from '../components/RunDetailModal'
import { StatsRow } from '../components/StatsRow'

export function StrategyList() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState('created_at')

  const { data: runs = [], isLoading } = useRuns(
    {
      sort_by: sortBy,
      order: 'desc',
    },
    5000
  )

  const deleteRun = useDeleteRun()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[var(--color-text-muted)]">Loading runs...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Row */}
      <StatsRow runs={runs} />

      {/* Sort Controls */}
      <div className="flex items-center gap-4">
        <label className="text-[var(--color-text-muted)] text-sm">Sort by:</label>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded px-3 py-1.5 text-sm text-[var(--color-text-primary)]"
        >
          <option value="created_at">Date</option>
          <option value="total_return">Return</option>
          <option value="sharpe_ratio">Sharpe</option>
          <option value="max_drawdown">Drawdown</option>
        </select>
      </div>

      {/* Runs Table */}
      <RunsTable
        runs={runs}
        onViewRun={setSelectedRunId}
        onDeleteRun={(id) => deleteRun.mutate(id)}
      />

      {/* Run Detail Modal */}
      {selectedRunId && (
        <RunDetailModal
          runId={selectedRunId}
          onClose={() => setSelectedRunId(null)}
        />
      )}
    </div>
  )
}
