import React from 'react'

export interface SyntheticDataBannerProps {
  scope?: string
}

export function SyntheticDataBanner({ scope = 'Pilot Demo' }: SyntheticDataBannerProps) {
  return (
    <div
      role="status"
      aria-label="Synthetic Demo Data Notice"
      className="w-full rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-200 flex items-center justify-between gap-3"
    >
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center rounded-md bg-amber-500/20 px-2 py-0.5 font-semibold uppercase tracking-wider text-amber-300 border border-amber-400/30">
          Synthetic Demo Data
        </span>
        <span>
          <strong>{scope}:</strong> All metrics, charts, and activity feeds displayed in this dashboard are synthetic demonstration figures. Partner mission data is isolated in the Engine API (<code>api.cashclaw.cc</code>).
        </span>
      </div>
      <span className="hidden sm:inline text-[11px] font-mono text-amber-300/80 shrink-0">
        INVITE-ONLY PILOT
      </span>
    </div>
  )
}

export function SyntheticMetricBadge({ label = 'Synthetic' }: { label?: string }) {
  return (
    <span
      title="Synthetic demo metric — no partner mission data"
      className="inline-flex items-center rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-300 border border-amber-500/30"
    >
      {label}
    </span>
  )
}
