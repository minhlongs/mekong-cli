const FEATURES = [
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.699-1.29 2.34l-1.407-.352M5 14.5l-1.402 1.402c-1 1-.03 2.699 1.29 2.34l1.407-.352" />
      </svg>
    ),
    color: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
    title: 'Plan → Execute → Verify',
    desc: 'AI plans tasks, decomposes them, executes step-by-step, then self-verifies quality before delivery.',
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
      </svg>
    ),
    color: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
    title: 'Self-Healing Pipeline',
    desc: 'Failed steps are auto-diagnosed and corrected. No manual intervention — the agent retries until success.',
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    title: 'Open Source 100%',
    desc: 'MIT License. Fork it, self-host, customize agents. Zero vendor lock-in — use any LLM provider.',
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
      </svg>
    ),
    color: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
    title: 'Pay Per Result',
    desc: '1 credit for simple tasks, 3 standard, 5 complex. Charged only after successful delivery — never upfront.',
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
    color: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
    title: '5 Business Layers',
    desc: 'Founder → Business → Product → Engineering → Ops. Each layer has specialized agents ready to execute.',
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
    color: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
    title: 'Automatic Cascade',
    desc: 'High-level goals decompose into parallel tasks across agents — Founder goals flow all the way to Ops.',
  },
]

export default function FeaturesGrid() {
  return (
    <section id="features" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Core capabilities
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Why choose{' '}
            <span className="gradient-text">Mekong CLI?</span>
          </h2>
          <p className="mx-auto max-w-xl text-slate-400">
            Self-governing infrastructure for AI agents — open-source core, pay-per-result delivery.
          </p>
        </div>

        {/* Grid */}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group relative overflow-hidden rounded-2xl border border-slate-800/60 bg-slate-900/40 p-6 transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/60 hover:-translate-y-1 hover:shadow-xl hover:shadow-black/20"
            >
              {/* Icon */}
              <div className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl border ${f.color}`}>
                {f.icon}
              </div>

              <h3 className="mb-2 font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{f.desc}</p>

              {/* Hover accent line */}
              <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}
