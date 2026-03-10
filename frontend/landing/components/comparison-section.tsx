const ROWS = [
  {
    role: '👑 Founder',
    single: 'Spreadsheet riêng',
    mekong: '/annual → auto cascade',
  },
  {
    role: '🏢 Sales',
    single: 'CRM riêng',
    mekong: '/sales → linked to OKR',
  },
  {
    role: '📦 Product',
    single: 'Jira / Linear',
    mekong: '/sprint → từ founder goal',
  },
  {
    role: '⚙️ Dev',
    single: 'Code không context',
    mekong: '/cook → biết phục vụ goal nào',
  },
  {
    role: '🔧 Ops',
    single: 'Monitor riêng',
    mekong: '/health → full lineage trace',
  },
]

export default function ComparisonSection() {
  return (
    <section id="comparison" className="px-6 py-20">
      <div className="mx-auto max-w-3xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Tại sao không dùng{' '}
            <span className="text-slate-500 line-through">tool đơn lẻ</span>?
          </h2>
          <p className="text-slate-400">
            Mỗi tầng dùng tool riêng = không ai hiểu context của nhau.
            Mekong CLI nối liền tất cả.
          </p>
        </div>

        <div className="glass-card overflow-hidden rounded-2xl">
          {/* Table header */}
          <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-900/60 px-6 py-3 text-xs font-semibold uppercase tracking-wider">
            <span className="text-slate-500">Vai trò</span>
            <span className="text-slate-500">Tool đơn lẻ</span>
            <span className="gradient-text">Mekong CLI</span>
          </div>

          {/* Rows */}
          {ROWS.map((row, i) => (
            <div
              key={i}
              className={`grid grid-cols-3 items-center px-6 py-4 text-sm ${
                i < ROWS.length - 1 ? 'border-b border-slate-800/60' : ''
              }`}
            >
              <span className="font-medium text-white">{row.role}</span>
              <span className="text-slate-500">{row.single}</span>
              <span className="font-mono text-cyan-400">{row.mekong}</span>
            </div>
          ))}
        </div>

        <p className="mt-6 text-center text-xs text-slate-600">
          Tất cả commands chia sẻ cùng context — không bao giờ lạc mục tiêu.
        </p>
      </div>
    </section>
  )
}
