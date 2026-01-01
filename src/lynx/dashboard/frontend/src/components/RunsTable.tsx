import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type ColumnDef,
} from '@tanstack/react-table'
import { useState, useMemo } from 'react'
import type { RunSummary } from '../types/api'

interface RunsTableProps {
  runs: RunSummary[]
  onViewRun: (runId: string) => void
  onDeleteRun: (runId: string) => void
  hideStrategyColumn?: boolean
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

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

const columnHelper = createColumnHelper<RunSummary>()

export function RunsTable({ runs, onViewRun, onDeleteRun, hideStrategyColumn = false }: RunsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const cols: ColumnDef<RunSummary, any>[] = []

    if (!hideStrategyColumn) {
      cols.push(columnHelper.accessor('strategy_name', {
        header: 'Strategy',
        cell: (info) => (
          <span className="bg-[var(--color-accent)]/20 text-[var(--color-accent)] px-2 py-1 rounded text-sm">
            {info.getValue()}
          </span>
        ),
      }))
    }

    cols.push(
      columnHelper.accessor('created_at', {
        header: 'Date',
        cell: (info) => (
          <div>
            <div className="text-[var(--color-text-secondary)] text-sm">
              {formatRelativeTime(info.getValue())}
            </div>
            <div className="text-[var(--color-text-muted)] text-xs font-mono">
              {info.row.original.id}
            </div>
          </div>
        ),
      }),
      columnHelper.accessor((row) => row.metrics?.total_return, {
        id: 'total_return',
        header: 'Return',
        cell: (info) => {
          const value = info.getValue()
          const isPositive = (value ?? 0) >= 0
          return (
            <span className={isPositive ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]'}>
              {formatPercent(value)}
            </span>
          )
        },
      }),
      columnHelper.accessor((row) => row.metrics?.sharpe_ratio, {
        id: 'sharpe_ratio',
        header: 'Sharpe',
        cell: (info) => formatNumber(info.getValue()),
      }),
      columnHelper.accessor((row) => row.metrics?.max_drawdown, {
        id: 'max_drawdown',
        header: 'Drawdown',
        cell: (info) => (
          <span className="text-[var(--color-negative)]">
            {formatPercent(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor((row) => row.metrics?.num_trades, {
        id: 'num_trades',
        header: 'Trades',
        cell: (info) => info.getValue() ?? 0,
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: (info) => (
          <div className="flex gap-2">
            <button
              onClick={() => onViewRun(info.row.original.id)}
              className="px-3 py-1 text-sm border border-[var(--color-border)] rounded text-[var(--color-text-secondary)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-colors"
            >
              View
            </button>
            <button
              onClick={() => {
                if (confirm(`Delete run ${info.row.original.id}?`)) {
                  onDeleteRun(info.row.original.id)
                }
              }}
              className="px-3 py-1 text-sm border border-[var(--color-border)] rounded text-[var(--color-text-secondary)] hover:border-[var(--color-negative)] hover:text-[var(--color-negative)] transition-colors"
            >
              Delete
            </button>
          </div>
        ),
      })
    )

    return cols
  }, [hideStrategyColumn, onViewRun, onDeleteRun])

  const table = useReactTable({
    data: runs,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (runs.length === 0) {
    return (
      <div className="bg-[var(--color-bg-secondary)] rounded-xl p-8 text-center">
        <h3 className="text-[var(--color-text-secondary)] text-lg mb-2">No runs yet</h3>
        <p className="text-[var(--color-text-muted)]">
          Log your first backtest with{' '}
          <code className="bg-[var(--color-bg-primary)] px-2 py-1 rounded text-sm">
            lynx.log("strategy", trades=df)
          </code>
        </p>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className="bg-[var(--color-bg-primary)] px-4 py-3 text-left text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider cursor-pointer hover:text-[var(--color-accent)] select-none"
                >
                  <div className="flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{
                      asc: ' ▲',
                      desc: ' ▼',
                    }[header.column.getIsSorted() as string] ?? null}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="hover:bg-[var(--color-bg-tertiary)] transition-colors"
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  className="px-4 py-3 border-t border-[var(--color-bg-primary)]"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
