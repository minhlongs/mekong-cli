const STEPS = [
  {
    role: '👑 Founder',
    cmd: '$ mekong annual "Kế hoạch 2026"',
    out: 'Q1: Launch Feature X, $250K ARR',
    color: 'text-yellow-400',
    border: 'border-yellow-500/25',
    bg: 'bg-yellow-500/5',
    dot: 'bg-yellow-400',
  },
  {
    role: '🏢 Business',
    cmd: '$ mekong sales "Q1 target $250K"',
    out: 'Pipeline: 50 leads, 10 demos',
    color: 'text-blue-400',
    border: 'border-blue-500/25',
    bg: 'bg-blue-500/5',
    dot: 'bg-blue-400',
  },
  {
    role: '📦 Product',
    cmd: '$ mekong roadmap "Feature X"',
    out: 'Sprint 1: Auth, Sprint 2: Dashboard',
    color: 'text-purple-400',
    border: 'border-purple-500/25',
    bg: 'bg-purple-500/5',
    dot: 'bg-purple-400',
  },
  {
    role: '⚙️ Engineering',
    cmd: '$ mekong cook "JWT auth service"',
    out: 'Plan → Execute → Verify ✓',
    color: 'text-cyan-400',
    border: 'border-cyan-500/25',
    bg: 'bg-cyan-500/5',
    dot: 'bg-cyan-400',
  },
  {
    role: '🔧 Ops',
    cmd: '$ mekong deploy-staging',
    out: '✓ Deployed. Health: 100%',
    color: 'text-emerald-400',
    border: 'border-emerald-500/25',
    bg: 'bg-emerald-500/5',
    dot: 'bg-emerald-400',
  },
]

export default function CascadeDemo() {
  return (
    <section id="cascade" className="px-6 py-20">
      <div className="mx-auto max-w-2xl">

        {/* Header */}
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Automatic cascade
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Strategy flows down{' '}
            <span className="gradient-text">every layer</span>
          </h2>
          <p className="text-slate-400">
            Founder goals automatically propagate — no meetings, no emails, no context loss.
          </p>
        </div>

        {/* Cascade steps */}
        <div className="flex flex-col items-center">
          {STEPS.map((step, i) => (
            <div key={i} className="flex w-full flex-col items-center">
              {/* Card */}
              <div
                className={`w-full rounded-2xl border p-5 ${step.border} ${step.bg} cascade-step backdrop-blur-sm`}
                style={{ animationDelay: `${i * 200}ms` }}
              >
                {/* Terminal header */}
                <div className="mb-3 flex items-center gap-2.5">
                  <div className="flex gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-green-500/60" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${step.dot}`} />
                    <span className={`text-xs font-semibold ${step.color}`}>
                      {step.role}
                    </span>
                  </div>
                </div>

                {/* Command */}
                <div className="mb-2 font-mono text-sm text-slate-300">
                  {step.cmd}
                </div>

                {/* Output */}
                <div className={`flex items-center gap-1.5 font-mono text-xs ${step.color}`}>
                  <span className="opacity-50">→</span>
                  {step.out}
                </div>
              </div>

              {/* Connector arrow */}
              {i < STEPS.length - 1 && (
                <div className="flex h-8 flex-col items-center justify-center gap-0.5">
                  <div className="h-4 w-px bg-gradient-to-b from-slate-700 to-slate-800" />
                  <svg className="h-3 w-3 text-slate-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 16l-6-6h12z" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

      </div>

      <style>{`
        @keyframes cascadeIn {
          from { opacity: 0; transform: translateX(-12px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .cascade-step {
          opacity: 0;
          animation: cascadeIn 0.45s ease both;
        }
      `}</style>
    </section>
  )
}
