const FEATURES = [
  {
    icon: '🧠',
    title: 'Plan → Execute → Verify',
    desc: 'AI plans, decomposes into tasks, executes step-by-step, and self-verifies quality.',
  },
  {
    icon: '🔄',
    title: 'Self-Healing Pipeline',
    desc: 'Failed steps are auto-diagnosed and corrected — no manual intervention needed.',
  },
  {
    icon: '🔓',
    title: 'Open Source 100%',
    desc: 'MIT License. Fork and run your own instance, customize agents, zero vendor lock-in.',
  },
  {
    icon: '💳',
    title: 'Pay per result',
    desc: '1 credit for simple tasks, 3 for standard, 5 for complex. Pay only on success.',
  },
  {
    icon: '🏯',
    title: '5 business layers',
    desc: 'Founder → Business → Product → Engineering → Ops. Each layer has specialized agents ready.',
  },
  {
    icon: '🌊',
    title: 'Automatic cascade',
    desc: 'High-level goals automatically decompose into parallel tasks across multiple agents.',
  },
]

export default function FeaturesGrid() {
  return (
    <section id="features" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Why choose{' '}
            <span className="gradient-text">Mekong CLI?</span>
          </h2>
          <p className="text-slate-400">
            Self-governing infrastructure for AI agents — open-source core, pay-per-result.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl glass-card p-6">
              <div className="mb-3 text-3xl">{f.icon}</div>
              <h3 className="mb-2 font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
