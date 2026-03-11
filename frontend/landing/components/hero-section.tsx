import SiteNav from '@/components/site-nav'
import { STATS } from '@/data/stats'

const HEADLINE = 'AI-Operated Business Platform'
const SUB = `Mekong CLI — ${STATS.commands} commands across 5 business layers. Universal LLM. Open source.`

export default function HeroSection() {
  return (
    <div>
      <SiteNav />
      <section className="relative px-6 pb-16 pt-16 text-center">
        <div className="mx-auto max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-800/40 bg-cyan-950/30 px-4 py-1.5 text-xs text-cyan-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
            Mekong CLI v5.0 · Open Source · MIT
          </div>

          <h1 className="mb-5 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            <span className="gradient-text">Agency</span>
            <span className="text-white">OS</span>
            <br />
            <span className="text-2xl font-bold text-slate-300 sm:text-3xl">{HEADLINE}</span>
          </h1>

          <p className="mx-auto mb-8 max-w-xl text-base text-slate-400 sm:text-lg">
            {SUB}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="#quickstart"
              className="rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-7 py-3 font-semibold text-white shadow-lg transition-opacity hover:opacity-90"
            >
              Get started free →
            </a>
            <a
              href="/pricing"
              className="rounded-xl border border-slate-700 px-7 py-3 font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
            >
              View pricing
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
