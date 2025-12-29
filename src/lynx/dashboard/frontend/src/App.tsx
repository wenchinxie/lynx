import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from './components/Header'
import { Controls } from './components/Controls'
import { StatsRow } from './components/StatsRow'
import { RunsTable } from './components/RunsTable'
import { RunDetailModal } from './components/RunDetailModal'
import { useRuns, useStrategies, useDeleteRun } from './hooks/useRuns'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      refetchOnWindowFocus: false,
    },
  },
})

function Dashboard() {
  const [selectedStrategy, setSelectedStrategy] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [pollInterval, setPollInterval] = useState(5000)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const { data: runs = [], dataUpdatedAt } = useRuns(
    {
      strategy: selectedStrategy || undefined,
      sort_by: sortBy,
      order: 'desc',
    },
    pollInterval
  )

  const { data: strategies = [] } = useStrategies()
  const deleteRun = useDeleteRun()

  // Update lastUpdate when data changes
  if (dataUpdatedAt && (!lastUpdate || dataUpdatedAt > lastUpdate.getTime())) {
    setLastUpdate(new Date(dataUpdatedAt))
  }

  return (
    <div className="min-h-screen p-6">
      <Header lastUpdate={lastUpdate} />

      <Controls
        strategies={strategies}
        selectedStrategy={selectedStrategy}
        onStrategyChange={setSelectedStrategy}
        sortBy={sortBy}
        onSortChange={setSortBy}
        pollInterval={pollInterval}
        onPollIntervalChange={setPollInterval}
      />

      <StatsRow runs={runs} />

      <RunsTable
        runs={runs}
        onViewRun={setSelectedRunId}
        onDeleteRun={(id) => deleteRun.mutate(id)}
      />

      {selectedRunId && (
        <RunDetailModal
          runId={selectedRunId}
          onClose={() => setSelectedRunId(null)}
        />
      )}
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}
