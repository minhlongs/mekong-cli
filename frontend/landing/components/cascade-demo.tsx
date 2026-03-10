const STEPS = [
  {
    role: '👑 Founder',
    cmd: '$ mekong annual "Kế hoạch 2026"',
    out: 'Q1: Launch Feature X, $250K ARR',
    color: 'text-yellow-400',
    border: 'border-yellow-500/30',
  },
  {
    role: '🏢 Business',
    cmd: '$ mekong sales "Q1 target $250K"',
    out: 'Pipeline: 50 leads, 10 demos',
    color: 'text-blue-400',
    border: 'border-blue-500/30',
  },
  {
    role: '📦 Product',
    cmd: '$ mekong roadmap "Feature X"',
    out: 'Sprint 1: Auth, Sprint 2: Dashboard',
    color: 'text-purple-400',
    border: 'border-purple-500/30',
  },
  {
    role: '⚙️ Engineering',
    cmd: '$ mekong cook "JWT auth service"',
    out: 'Plan → Execute → Verify ✓',
    color: 'text-cyan-400',
    border: 'border-cyan-500/30',
  },
  {
    role: '🔧 Ops',
    cmd: '$ mekong deploy-staging',
    out: '✓ Deployed. Health: 100%',
    color: 'text-green-400',
    border: 'border-green-500/30',
  },
]

export default function CascadeDemo() {
  return (
    <section id="cascade" className="px-6 py-20">
      <div className="mx-auto max-w-2xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Chiến lược{' '}
            <span className="gradient-text">cascade tự động</span>
          </h2>
          <p className="text-slate-400">
            Mục tiêu Founder tự động lan xuống từng tầng — không cần họp, không cần email.
          </p>
        </div>

        <div className="flex flex-col items-center gap-0">
          {STEPS.map((step, i) => (
            <div key={i} className="flex w-full flex-col items-center">
              <div
                className={`w-full glass-card rounded-2xl border p-5 ${step.border} cascade-step`}
                style={{ animationDelay: `${i * 300}ms` }}
              >
                {/* Terminal header */}
                <div className="mb-3 flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                    <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                    <span className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                  </div>
                  <span className={`ml-1 text-xs font-semibold ${step.color}`}>
                    {step.role}
                  </span>
                </div>
                {/* Command */}
                <div className="mb-2 font-mono text-sm text-slate-300">
                  {step.cmd}
                </div>
                {/* Output */}
                <div className={`font-mono text-xs ${step.color}`}>
                  → {step.out}
                </div>
              </div>

              {/* Arrow connector */}
              {i < STEPS.length - 1 && (
                <div className="flex h-8 flex-col items-center justify-center">
                  <div className="h-4 w-px bg-slate-700" />
                  <span className="text-xs text-slate-600">↓</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes cascadeIn {
          from { opacity: 0; transform: translateX(-16px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .cascade-step {
          opacity: 0;
          animation: cascadeIn 0.5s ease both;
        }
      `}</style>
    </section>
  )
}
