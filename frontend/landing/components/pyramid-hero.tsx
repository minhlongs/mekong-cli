'use client'

const LAYERS = [
  {
    id: 'founder',
    href: '/founder',
    icon: '👑',
    role: 'FOUNDER / CEO',
    desc: 'Strategy, fundraising, OKRs, dashboard',
    width: 'max-w-xs',
    delay: 'animation-delay-0',
    color: 'border-yellow-500/40 hover:border-yellow-400/60',
    glow: 'hover:shadow-yellow-500/10',
  },
  {
    id: 'business',
    href: '/business',
    icon: '🏢',
    role: 'BUSINESS',
    desc: 'Sales, marketing, finance, HR',
    width: 'max-w-sm',
    delay: 'animation-delay-200',
    color: 'border-blue-500/40 hover:border-blue-400/60',
    glow: 'hover:shadow-blue-500/10',
  },
  {
    id: 'product',
    href: '/product',
    icon: '📦',
    role: 'PRODUCT',
    desc: 'Product planning, sprints, roadmap',
    width: 'max-w-md',
    delay: 'animation-delay-400',
    color: 'border-purple-500/40 hover:border-purple-400/60',
    glow: 'hover:shadow-purple-500/10',
  },
  {
    id: 'developer',
    href: '/dev/quickstart',
    icon: '⚙️',
    role: 'DEVELOPER',
    desc: 'Code, test, deploy — get started in 5 minutes',
    width: 'max-w-lg',
    delay: 'animation-delay-600',
    color: 'border-cyan-500/40 hover:border-cyan-400/60',
    glow: 'hover:shadow-cyan-500/10',
  },
  {
    id: 'operations',
    href: '/ops',
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
          5-Layer Pyramid — Founder to Operations
        </div>

        <h1 className="mb-5 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl pyramid-fade-in">
          Run your business with AI —{' '}
          <span className="gradient-text">from strategy to code</span>
        </h1>

        <p className="mx-auto mb-14 max-w-2xl text-base text-slate-400 sm:text-lg pyramid-fade-in">
          <span className="font-mono text-cyan-400">289 commands.</span>{' '}
          <span className="font-mono text-indigo-400">216 skills.</span>{' '}
          <span className="font-mono text-purple-400">127 AI agents.</span>{' '}
          One unified system from Founder to Operations.
        </p>

        {/* Pyramid layers */}
        <div className="flex flex-col items-center gap-3">
          {LAYERS.map((layer, i) => (
            <a
              key={layer.id}
              href={layer.href}
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
            Get started free
          </a>
          <a
            href="https://github.com/longtho638-jpg/mekong-cli"
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
