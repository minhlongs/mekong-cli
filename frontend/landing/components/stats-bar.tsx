const STATS = [
  { value: '167', label: 'Commands' },
  { value: '464', label: 'AI Skills' },
  { value: '105', label: 'Subagents' },
  { value: '5', label: 'Tầng' },
  { value: '1,412', label: 'Commits' },
]

export default function StatsBar() {
  return (
    <section className="px-6 py-10">
      <div className="mx-auto max-w-5xl">
        <div className="glass-card rounded-2xl px-6 py-8">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-5">
            {STATS.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="gradient-text text-4xl font-extrabold leading-none">
                  {stat.value}
                </div>
                <div className="mt-2 text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
