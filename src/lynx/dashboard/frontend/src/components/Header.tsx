interface HeaderProps {
  lastUpdate: Date | null
}

export function Header({ lastUpdate }: HeaderProps) {
  const formatRelativeTime = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    return `${diffHours}h ago`
  }

  return (
    <header className="flex justify-between items-center mb-6 pb-4 border-b border-[var(--color-border)]">
      <h1 className="text-3xl font-bold bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-accent-light)] bg-clip-text text-transparent">
        Lynx Dashboard
      </h1>
      <div className="flex items-center gap-4 text-sm text-[var(--color-text-secondary)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[var(--color-positive)] animate-pulse" />
          <span>Auto-refresh</span>
        </div>
        <span className="text-[var(--color-text-muted)]">
          Updated {lastUpdate ? formatRelativeTime(lastUpdate) : 'never'}
        </span>
      </div>
    </header>
  )
}
