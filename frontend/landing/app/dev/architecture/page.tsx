import Link from 'next/link'
import SiteNav from '@/components/site-nav'

const TECH_STACK = [
  { layer: 'CLI', tech: 'Python / Typer / Rich', desc: 'Giao diện dòng lệnh, Rich UI, type hints' },
  { layer: 'API', tech: 'FastAPI / Cloudflare Workers', desc: 'Local gateway + edge deployment' },
  { layer: 'PEV', tech: 'src/core/ planner→executor→verifier', desc: 'Plan–Execute–Verify orchestration loop' },
  { layer: 'LLM', tech: 'Claude + Gemini + Qwen + Ollama', desc: 'Multi-model router qua Antigravity Proxy :9191' },
  { layer: 'DB', tech: 'Supabase (prod) / SQLite (dev)', desc: 'Persistent state, credits, mission log' },
  { layer: 'Billing', tech: 'Polar.sh + MCU credits', desc: '1 MCU = 1 credit, webhooks → src/raas/credits.py' },
]

const PEV_ASCII = `┌─────────┐    ┌─────────┐    ┌─────────┐
│  PLAN   │───▶│ EXECUTE │───▶│ VERIFY  │
│ Planner │    │Executor │    │Verifier │
│   LLM   │    │Shell/API│    │ Gates   │
└─────────┘    └─────────┘    └─────────┘
     │              │              │
     └──────────────┴──────────────┘
              Orchestrator`

const CASCADE_ASCII = `👑 Founder ──▶ 🏢 Business ──▶ 📦 Product ──▶ ⚙️ Engineering ──▶ 🔧 Ops
   /annual       /sales           /roadmap        /cook              /deploy`

const AGENT_ASCII = `              ┌──────────────────┐
              │   Orchestrator   │
              └────────┬─────────┘
          ┌────────────┼────────────┐
    ┌─────▼─────┐ ┌────▼─────┐ ┌───▼──────┐
    │  Planner  │ │ Executor │ │ Verifier │
    │ (LLM dec.)│ │ (shell)  │ │ (gates)  │
    └───────────┘ └──────────┘ └──────────┘

18 hubs · 105 agents · LLM Router: Claude / Gemini / Qwen / Ollama`

export default function ArchitecturePage() {
  return (
    <main className="min-h-screen bg-slate-950">
      <SiteNav />
      <div className="px-4 pb-16 pt-8 sm:px-6">
      <div className="mx-auto max-w-4xl">
        {/* Back nav */}
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
        >
          ← Trang chủ
        </Link>

        {/* Hero */}
        <div className="mb-12 text-center">
          <div className="mb-4 text-4xl">⚙️</div>
          <h1 className="mb-3 text-3xl font-bold sm:text-4xl">
            <span className="gradient-text">Architecture</span>
          </h1>
          <p className="text-lg text-slate-400">Kiến trúc hệ thống AgencyOS</p>
        </div>

        {/* Section 1: PEV Pipeline */}
        <section className="mb-10">
          <h2 className="mb-4 text-xl font-semibold text-slate-100">
            1. PEV Pipeline
          </h2>
          <p className="mb-4 text-sm text-slate-400">
            Mọi lệnh đều chạy qua 3 giai đoạn:{' '}
            <span className="text-cyan-400">Plan → Execute → Verify</span>.
            Orchestrator điều phối toàn bộ vòng lặp, tự động rollback khi
            verification thất bại.
          </p>
          <div className="glass-card rounded-xl p-5">
            <pre className="overflow-x-auto font-mono text-xs text-cyan-400 sm:text-sm">
              {PEV_ASCII}
            </pre>
          </div>
        </section>

        {/* Section 2: 5-Layer Cascade */}
        <section className="mb-10">
          <h2 className="mb-4 text-xl font-semibold text-slate-100">
            2. Kim Tự Tháp 5 Tầng
          </h2>
          <p className="mb-4 text-sm text-slate-400">
            Chiến lược từ Founder cascade xuống Ops. Mỗi tầng nhận output từ
            tầng trên và cung cấp input cho tầng dưới.
          </p>
          <div className="glass-card rounded-xl p-5">
            <pre className="overflow-x-auto font-mono text-xs text-cyan-400 sm:text-sm whitespace-pre">
              {CASCADE_ASCII}
            </pre>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[
              { icon: '👑', label: 'Founder', color: 'text-cyan-400' },
              { icon: '🏢', label: 'Business', color: 'text-blue-400' },
              { icon: '📦', label: 'Product', color: 'text-purple-400' },
              { icon: '⚙️', label: 'Engineering', color: 'text-green-400' },
              { icon: '🔧', label: 'Ops', color: 'text-orange-400' },
            ].map((l) => (
              <div key={l.label} className="glass-card rounded-lg p-3 text-center">
                <div className="text-xl">{l.icon}</div>
                <div className={`mt-1 text-xs font-medium ${l.color}`}>
                  {l.label}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 3: Agent Hierarchy */}
        <section className="mb-10">
          <h2 className="mb-4 text-xl font-semibold text-slate-100">
            3. Agent Hierarchy
          </h2>
          <p className="mb-4 text-sm text-slate-400">
            Orchestrator sinh ra các sub-agent chuyên biệt. 18 hub điều phối
            105 agent, mỗi agent chạy trên LLM phù hợp nhất.
          </p>
          <div className="glass-card rounded-xl p-5">
            <pre className="overflow-x-auto font-mono text-xs text-cyan-400 sm:text-sm">
              {AGENT_ASCII}
            </pre>
          </div>
        </section>

        {/* Section 4: Tech Stack */}
        <section className="mb-10">
          <h2 className="mb-4 text-xl font-semibold text-slate-100">
            4. Tech Stack
          </h2>
          <div className="glass-card overflow-hidden rounded-xl">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Layer
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Technology
                  </th>
                  <th className="hidden px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 sm:table-cell">
                    Mô tả
                  </th>
                </tr>
              </thead>
              <tbody>
                {TECH_STACK.map((row, i) => (
                  <tr
                    key={row.layer}
                    className={i < TECH_STACK.length - 1 ? 'border-b border-slate-800/60' : ''}
                  >
                    <td className="px-5 py-3 font-mono text-xs font-bold text-cyan-400 whitespace-nowrap">
                      {row.layer}
                    </td>
                    <td className="px-5 py-3 text-xs text-slate-300">
                      {row.tech}
                    </td>
                    <td className="hidden px-5 py-3 text-xs text-slate-500 sm:table-cell">
                      {row.desc}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Footer nav */}
        <div className="mt-4 flex flex-wrap gap-4 justify-center">
          <Link
            href="/dev/quickstart"
            className="glass-card rounded-lg px-5 py-2.5 text-sm text-slate-300 hover:text-cyan-400 transition-colors"
          >
            ← Quickstart
          </Link>
          <Link
            href="/dev/commands"
            className="glass-card rounded-lg px-5 py-2.5 text-sm text-slate-300 hover:text-cyan-400 transition-colors"
          >
            ← Command Explorer
          </Link>
        </div>
      </div>
      </div>
    </main>
  )
}
