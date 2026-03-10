'use client'

const LAYERS = [
  {
    id: 'founder',
    icon: '👑',
    role: 'FOUNDER / CEO',
    desc: 'Lập kế hoạch, gọi vốn, OKR, dashboard',
    width: 'max-w-xs',
    delay: 'animation-delay-0',
    color: 'border-yellow-500/40 hover:border-yellow-400/60',
    glow: 'hover:shadow-yellow-500/10',
  },
  {
    id: 'business',
    icon: '🏢',
    role: 'BUSINESS',
    desc: 'Sales, marketing, tài chính, nhân sự',
    width: 'max-w-sm',
    delay: 'animation-delay-200',
    color: 'border-blue-500/40 hover:border-blue-400/60',
    glow: 'hover:shadow-blue-500/10',
  },
  {
    id: 'product',
    icon: '📦',
    role: 'PRODUCT',
    desc: 'Lập kế hoạch sản phẩm, sprint, roadmap',
    width: 'max-w-md',
    delay: 'animation-delay-400',
    color: 'border-purple-500/40 hover:border-purple-400/60',
    glow: 'hover:shadow-purple-500/10',
  },
  {
    id: 'developer',
    icon: '⚙️',
    role: 'DEVELOPER',
    desc: 'Code, test, deploy — bắt đầu trong 5 phút',
    width: 'max-w-lg',
    delay: 'animation-delay-600',
    color: 'border-cyan-500/40 hover:border-cyan-400/60',
    glow: 'hover:shadow-cyan-500/10',
  },
  {
    id: 'operations',
    icon: '🔧',
    role: 'OPERATIONS',
    desc: 'Monitor, audit, sync, recovery',
    width: 'max-w-2xl',
    delay: 'animation-delay-800',
    color: 'border-green-500/40 hover:border-green-400/60',
    glow: 'hover:shadow-green-500/10',
  },
]

export default function PyramidHero() {
  return (
    <section className="relative overflow-hidden px-6 py-20 text-center">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-600/5 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-4xl">
        {/* Headline */}
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-4 py-1.5 text-xs text-slate-400">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
          Kim Tự Tháp 5 Tầng — Từ Founder đến Operations
        </div>

        <h1 className="mb-5 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl pyramid-fade-in">
          Vận hành doanh nghiệp bằng AI —{' '}
          <span className="gradient-text">Từ chiến lược đến code</span>
        </h1>

        <p className="mx-auto mb-14 max-w-2xl text-base text-slate-400 sm:text-lg pyramid-fade-in">
          <span className="font-mono text-cyan-400">167 commands.</span>{' '}
          <span className="font-mono text-indigo-400">464 skills.</span>{' '}
          <span className="font-mono text-purple-400">105 AI agents.</span>{' '}
          Một hệ thống thống nhất từ Founder đến Developer.
        </p>

        {/* Pyramid layers */}
        <div className="flex flex-col items-center gap-3">
          {LAYERS.map((layer, i) => (
            <a
              key={layer.id}
              href={`#${layer.id}`}
              className={[
                'w-full glass-card rounded-2xl p-4 transition-all duration-300',
                layer.width,
                layer.color,
                layer.glow,
                'hover:shadow-lg',
                'pyramid-layer-anim',
              ].join(' ')}
              style={{ animationDelay: `${i * 200}ms` }}
            >
              <div className="flex items-center justify-center gap-3">
                <span className="text-2xl">{layer.icon}</span>
                <div className="text-left">
                  <div className="text-sm font-bold tracking-widest text-white">
                    {layer.role}
                  </div>
                  <div className="text-xs text-slate-400">{layer.desc}</div>
                </div>
              </div>
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
          <a
            href="#quickstart"
            className="rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-8 py-3.5 font-semibold text-white shadow-lg transition-opacity hover:opacity-90"
          >
            Bắt đầu miễn phí
          </a>
          <a
            href="https://github.com/agencyos/mekong-cli"
            className="rounded-xl border border-slate-700 bg-slate-900 px-8 py-3.5 font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
          >
            ★ GitHub
          </a>
        </div>
      </div>

      <style>{`
        @keyframes pyramidFadeIn {
          from { opacity: 0; transform: translateY(-20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .pyramid-fade-in {
          animation: pyramidFadeIn 0.7s ease both;
        }
        .pyramid-layer-anim {
          opacity: 0;
          animation: pyramidFadeIn 0.6s ease both;
        }
      `}</style>
    </section>
  )
}
