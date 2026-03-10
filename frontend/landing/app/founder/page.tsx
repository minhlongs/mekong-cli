import LayerPageHero from '@/components/layer-page-hero'
import CommandGrid from '@/components/command-grid'
import SiteNav from '@/components/site-nav'
import { COMMANDS } from '@/data/commands'
import { LAYERS } from '@/data/layers'
import Link from 'next/link'

const founderLayer = LAYERS.find((l) => l.id === 'founder')!
const founderCommands = COMMANDS.filter((c) => c.layer === 'founder')

export default function FounderPage() {
  return (
    <main className="min-h-screen bg-slate-950">
      <SiteNav />
      <LayerPageHero
        icon={founderLayer.icon}
        title="Founder Command Center"
        subtitle="13 commands để vận hành chiến lược. AI agents làm phần còn lại."
        commandCount={founderCommands.length}
        color={founderLayer.color}
      />

      {/* Commands grid */}
      <section className="px-6 pb-16">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-6 text-xl font-bold text-white">
            Tất cả Founder Commands
          </h2>
          <CommandGrid commands={founderCommands} columns={3} />
        </div>
      </section>

      {/* Cascade section */}
      <section className="px-6 pb-16">
        <div className="mx-auto max-w-5xl">
          <div className="glass-highlight rounded-2xl p-8">
            <h2 className="mb-3 text-xl font-bold text-white">
              Cascade Intelligence
            </h2>
            <p className="mb-6 text-slate-400">
              Khi bạn chạy <code className="font-mono text-cyan-300">/annual</code>, AI cascade xuống toàn bộ công ty — không cần giao việc thủ công.
            </p>
            <div className="flex flex-wrap items-center gap-3 font-mono text-sm">
              {['👑 /annual', '→', '🏢 Business', '→', '📦 Product', '→', '⚙️ Engineering', '→', '🔧 Ops'].map(
                (item, i) => (
                  <span
                    key={i}
                    className={
                      item === '→'
                        ? 'text-slate-500'
                        : 'rounded-lg border border-cyan-800/50 bg-cyan-950/30 px-3 py-1.5 text-cyan-300'
                    }
                  >
                    {item}
                  </span>
                )
              )}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20 text-center">
        <Link
          href="/#quickstart"
          className="inline-block rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-8 py-3.5 font-semibold text-white shadow-lg transition-opacity hover:opacity-90"
        >
          Bắt đầu ngay →
        </Link>
      </section>
    </main>
  )
}
