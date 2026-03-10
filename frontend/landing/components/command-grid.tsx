interface CommandItem {
  id: string
  displayName: string
  description: string
  creditCost: number
}

interface CommandGridProps {
  commands: CommandItem[]
  columns?: number
}

function CreditBadge({ cost }: { cost: number }) {
  if (cost === 0) {
    return (
      <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
        free
      </span>
    )
  }
  const dots = Math.min(cost, 5)
  return (
    <span className="rounded-full border border-cyan-900 bg-cyan-950/50 px-2 py-0.5 font-mono text-xs text-cyan-400">
      {'●'.repeat(dots)}
    </span>
  )
}

export default function CommandGrid({ commands, columns = 3 }: CommandGridProps) {
  const gridClass =
    columns === 2
      ? 'grid gap-3 sm:grid-cols-2'
      : columns === 4
        ? 'grid gap-3 sm:grid-cols-2 lg:grid-cols-4'
        : 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3'

  return (
    <div className={gridClass}>
      {commands.map((cmd) => (
        <div
          key={cmd.id}
          className="glass-card flex flex-col gap-1.5 rounded-xl p-4"
        >
          <div className="flex items-start justify-between gap-2">
            <code className="font-mono text-sm font-semibold text-cyan-300">
              /{cmd.id}
            </code>
            <CreditBadge cost={cmd.creditCost} />
          </div>
          <p className="text-xs leading-relaxed text-slate-400 line-clamp-2">
            {cmd.description}
          </p>
        </div>
      ))}
    </div>
  )
}
