import { useEffect } from 'react'
import { useRunDetail, useRunMetrics, useRunMonthlyReturns } from '../hooks/useRunDetail'
import { MetricsTabs } from './MetricsTabs'
import { SingleRunHeatmap } from './SingleRunHeatmap'

interface RunDetailModalProps {
  runId: string | null
  onClose: () => void
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleString()
}

export function RunDetailModal({ runId, onClose }: RunDetailModalProps) {
  const { data: run, isLoading: runLoading } = useRunDetail(runId)
  const { data: metrics, isLoading: metricsLoading } = useRunMetrics(runId)
  const { data: monthlyReturns, isLoading: monthlyLoading } = useRunMonthlyReturns(runId)

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!runId) return null

  const isLoading = runLoading || metricsLoading

  return (
    <div
      className="fixed inset-0 bg-black/70 flex justify-center items-center z-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-[var(--color-bg-secondary)] rounded-xl p-6 w-[95%] max-w-[1600px] max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-[var(--color-accent)]">
            {run?.strategy_name ?? 'Loading...'}
          </h2>
          <button
            onClick={onClose}
            className="text-2xl text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            &times;
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-[var(--color-text-secondary)]">
            Loading...
          </div>
        ) : run ? (
          <>
            {/* Run ID and timestamps */}
            <p className="text-sm font-mono text-[var(--color-text-muted)] mb-4">
              {run.id}
            </p>
            <div className="flex gap-4 mb-6 text-sm text-[var(--color-text-secondary)]">
              <span>Created: {formatDate(run.created_at)}</span>
              <span>Updated: {formatDate(run.updated_at)}</span>
            </div>

            {/* Metrics Tabs */}
            {metrics && (
              <div className="mb-6">
                <MetricsTabs data={metrics} />
              </div>
            )}

            {/* Monthly Returns Heatmap */}
            <div className="mb-6">
              <SingleRunHeatmap data={monthlyReturns} isLoading={monthlyLoading} />
            </div>

            {/* Parameters */}
            <div className="bg-[var(--color-bg-primary)] rounded-lg p-4 mb-4">
              <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                Parameters
              </h4>
              <div className="font-mono text-sm">
                {Object.entries(run.params || {}).length > 0 ? (
                  Object.entries(run.params).map(([k, v]) => (
                    <div key={k}>
                      <strong>{k}:</strong> {JSON.stringify(v)}
                    </div>
                  ))
                ) : (
                  <div className="text-[var(--color-text-muted)]">No parameters</div>
                )}
              </div>
            </div>

            {/* Artifacts */}
            <div className="bg-[var(--color-bg-primary)] rounded-lg p-4">
              <h4 className="text-sm text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                Artifacts
              </h4>
              <div className="font-mono text-sm">
                {run.artifacts && run.artifacts.length > 0 ? (
                  run.artifacts.map((artifact) => (
                    <div key={artifact}>{artifact}</div>
                  ))
                ) : (
                  <div className="text-[var(--color-text-muted)]">No artifacts</div>
                )}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
