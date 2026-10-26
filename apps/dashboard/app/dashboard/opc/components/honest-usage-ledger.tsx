'use client'

import React from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { Scale, AlertOctagon, CheckCircle2 } from 'lucide-react'
import type { OpcUsageEvent, SupportedCurrency, UsageStage } from '@/lib/opc-cockpit-data'

interface HonestUsageLedgerProps {
  runId: string
  currency: SupportedCurrency
  events: OpcUsageEvent[]
  hasUnknownCosts: boolean
  knownTotal: number
}

const STAGE_STYLES: Record<UsageStage, { label: string; badge: string }> = {
  estimated: {
    label: 'ESTIMATED',
    badge: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  },
  reserved: {
    label: 'RESERVED',
    badge: 'border-purple-500/30 bg-purple-500/10 text-purple-300',
  },
  actual: {
    label: 'ACTUAL',
    badge: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  unknown: {
    label: 'UNKNOWN',
    badge: 'border-amber-500/40 bg-amber-500/15 text-amber-300',
  },
}

export default function HonestUsageLedger({
  runId,
  currency,
  events,
  hasUnknownCosts,
  knownTotal,
}: HonestUsageLedgerProps) {
  const totalTokens = events.reduce((acc, ev) => acc + ev.tokens, 0)

  return (
    <AgencyCard variant="glass" className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <Scale className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">04 · Honest Usage & Economics Ledger</h3>
            <p className="text-[11px] text-neutral-500">
              4 stages (<code className="text-neutral-300">estimated</code>,{' '}
              <code className="text-neutral-300">reserved</code>,{' '}
              <code className="text-neutral-300">actual</code>,{' '}
              <code className="text-neutral-300">unknown</code>). Never coerces unknown to zero.
            </p>
          </div>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold ${
            hasUnknownCosts
              ? 'border border-amber-500/40 bg-amber-500/15 text-amber-300'
              : 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
          }`}
        >
          has_unknown_costs: {String(hasUnknownCosts)}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-500">Known Amount</div>
          <div className="text-sm font-mono font-bold text-emerald-400 mt-1">
            {knownTotal.toFixed(2)} {currency}
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-500">Total Tokens</div>
          <div className="text-sm font-mono font-bold text-white mt-1">{totalTokens.toLocaleString()}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-500">Ledger Events</div>
          <div className="text-sm font-mono font-bold text-white mt-1">{events.length}</div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
          opc_usage_events ({runId})
        </div>
        {events.map((ev) => {
          const st = STAGE_STYLES[ev.stage]
          return (
            <div
              key={ev.event_id}
              className="flex items-center justify-between rounded-lg border border-white/5 bg-[#06080d] px-3.5 py-2.5 text-xs font-mono"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className={`rounded px-2 py-0.5 text-[10px] border font-bold ${st.badge}`}>
                  {st.label}
                </span>
                <div className="truncate">
                  <div className="text-white text-xs">{ev.provider} · {ev.model}</div>
                  <div className="text-[10px] text-neutral-500">
                    {ev.event_id} · source: {ev.pricing_source} · {ev.tokens} tok
                  </div>
                </div>
              </div>
              <div className="text-right shrink-0 ml-2">
                {ev.amount === null || ev.stage === 'unknown' ? (
                  <span className="text-amber-400 font-bold text-[11px]">NULL (UNKNOWN)</span>
                ) : (
                  <span className="text-emerald-400 font-bold">
                    {ev.amount} {ev.currency}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {hasUnknownCosts ? (
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 flex items-start gap-2.5 text-[11px] text-amber-200">
          <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Truthful Economics Invariant Active:</span> At least one usage event has{' '}
            <code className="text-amber-300">stage=&quot;unknown&quot;</code> or <code className="text-amber-300">amount=None</code>.
            The ledger surfaces <code className="text-amber-300">has_unknown_costs=True</code> instead of silently reporting $0.00.
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 flex items-center gap-2 text-[11px] text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          100% of execution and connector stages have deterministic known costs.
        </div>
      )}
    </AgencyCard>
  )
}
