const STEPS = [
  {
    number: '01',
    title: 'Describe your goal',
    desc: 'Enter your goal in plain text. Example: "Create a landing page for a café".',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
      </svg>
    ),
    color: 'from-blue-500 to-blue-600',
    glow: 'shadow-blue-500/30',
    accent: 'border-blue-500/30 bg-blue-500/5',
  },
  {
    number: '02',
    title: 'Pay credits',
    desc: '3 credits = standard task (~$15). Only charged after successful delivery.',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
      </svg>
    ),
    color: 'from-purple-500 to-purple-600',
    glow: 'shadow-purple-500/30',
    accent: 'border-purple-500/30 bg-purple-500/5',
  },
  {
    number: '03',
    title: 'AI executes',
    desc: 'Plan → Execute → Verify fully automated. Tôm Hùm agent self-heals on errors.',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.699-1.29 2.34l-1.407-.352M5 14.5l-1.402 1.402c-1 1-.03 2.699 1.29 2.34l1.407-.352" />
      </svg>
    ),
    color: 'from-cyan-500 to-cyan-600',
    glow: 'shadow-cyan-500/30',
    accent: 'border-cyan-500/30 bg-cyan-500/5',
  },
  {
    number: '04',
    title: 'Get results',
    desc: 'Files + links ready in 15 minutes. Full audit trail of every execution step.',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'from-emerald-500 to-emerald-600',
    glow: 'shadow-emerald-500/30',
    accent: 'border-emerald-500/30 bg-emerald-500/5',
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Simple process
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            From goal to delivery in{' '}
            <span className="gradient-text">4 steps</span>
          </h2>
          <p className="text-slate-400">
            No setup, no waiting. Describe it — the AI handles the rest.
          </p>
        </div>

        {/* Steps */}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <div
              key={step.number}
              className={`relative rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 ${step.accent}`}
            >
              {/* Step number + connector */}
              <div className="mb-5 flex items-center gap-3">
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${step.color} shadow-lg ${step.glow} text-white`}>
                  {step.icon}
                </div>
                {i < STEPS.length - 1 && (
                  <div className="hidden h-px flex-1 bg-gradient-to-r from-slate-700 to-transparent lg:block" />
                )}
              </div>

              {/* Step label */}
              <div className="mb-1.5 font-mono text-xs font-semibold tracking-widest text-slate-500">
                STEP {step.number}
              </div>

              <h3 className="mb-2 font-semibold text-white">{step.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{step.desc}</p>
            </div>
          ))}
        </div>

        {/* Bottom callout */}
        <div className="mt-10 rounded-xl border border-slate-800/60 bg-slate-900/40 px-6 py-4 text-center">
          <p className="text-sm text-slate-400">
            <span className="font-mono text-cyan-400">Plan → Execute → Verify</span>
            {' '}— every task is auditable. Full logs, no black boxes.
          </p>
        </div>

      </div>
    </section>
  )
}
