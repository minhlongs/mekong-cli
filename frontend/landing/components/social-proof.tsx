import { TESTIMONIALS } from '@/data/testimonials'
import { STATS } from '@/data/stats'

export default function SocialProof() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-5xl">
        {/* Stats callout */}
        <div className="mb-12 text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-400">
            Trusted by builders
          </p>
          <p className="mt-2 text-3xl font-bold text-white">
            {STATS.commands}+ commands powering solo founders &amp; teams
          </p>
        </div>

        {/* Testimonial cards */}
        <div className="grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <div
              key={t.name}
              className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6"
            >
              <p className="mb-4 text-sm leading-relaxed text-slate-300">
                &ldquo;{t.quote}&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-900/40 text-xs font-bold text-cyan-400">
                  {t.initials}
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{t.name}</p>
                  <p className="text-xs text-slate-500">
                    {t.role}, {t.company}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
