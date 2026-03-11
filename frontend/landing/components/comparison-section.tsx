const ROWS = [
  {
    role: 'Founder',
    roleIcon: '👑',
    single: 'Spreadsheet silo',
    mekong: '/annual → auto cascade',
  },
  {
    role: 'Sales',
    roleIcon: '🏢',
    single: 'Standalone CRM',
    mekong: '/sales → linked to OKR',
  },
  {
    role: 'Product',
    roleIcon: '📦',
    single: 'Jira / Linear',
    mekong: '/sprint → from founder goal',
  },
  {
    role: 'Dev',
    roleIcon: '⚙️',
    single: 'Code without context',
    mekong: '/cook → knows which goal it serves',
  },
  {
    role: 'Ops',
    roleIcon: '🔧',
    single: 'Separate monitoring',
    mekong: '/health → full lineage trace',
  },
]

export default function ComparisonSection() {
  return (
    <section id="comparison" className="px-6 py-20">
      <div className="mx-auto max-w-3xl">

        {/* Header */}
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Why not separate tools?
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Every layer{' '}
            <span className="text-slate-500 line-through decoration-red-500/60">siloed</span>
            {' '}vs{' '}
            <span className="gradient-text">connected</span>
          </h2>
          <p className="text-slate-400">
            Separate tools mean no shared context. Mekong CLI threads a single goal through every layer.
          </p>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-2xl border border-slate-800/60">
          {/* Header row */}
          <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-900/80 px-6 py-3.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Layer</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Separate tools</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Mekong CLI</span>
          </div>

          {/* Data rows */}
          {ROWS.map((row, i) => (
            <div
              key={i}
              className={`grid grid-cols-3 items-center px-6 py-4 text-sm transition-colors hover:bg-slate-900/40 ${
                i < ROWS.length - 1 ? 'border-b border-slate-800/50' : ''
              }`}
            >
              <span className="flex items-center gap-2 font-medium text-white">
                <span>{row.roleIcon}</span>
                {row.role}
              </span>
              <span className="flex items-center gap-1.5 text-slate-500">
                <svg className="h-3.5 w-3.5 shrink-0 text-red-500/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                {row.single}
              </span>
              <span className="font-mono text-xs text-cyan-400">{row.mekong}</span>
            </div>
          ))}
        </div>

        <p className="mt-5 text-center text-xs text-slate-600">
          All commands share full context — never lose sight of the goal.
        </p>

      </div>
    </section>
  )
}
