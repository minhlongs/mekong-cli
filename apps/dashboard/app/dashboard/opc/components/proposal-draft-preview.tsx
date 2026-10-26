'use client'

import React from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { FileText, AlertTriangle, CheckCircle2 } from 'lucide-react'
import type { OpcLineItem, SupportedCurrency, SupportedLanguage } from '@/lib/opc-cockpit-data'
import { SERVICE_CATALOG } from '@/lib/opc-cockpit-data'

interface ProposalDraftPreviewProps {
  runId: string
  packId: string
  clientName: string
  clientContact: string
  projectTitle: string
  principal: string
  currency: SupportedCurrency
  language: SupportedLanguage
  lineItems: OpcLineItem[]
  totalAmount: number
  missingFields: string[]
}

const formatMoney = (amount: number, currency: SupportedCurrency): string => {
  if (currency === 'VND') {
    return `${Math.round(amount).toLocaleString('vi-VN')} ₫`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export default function ProposalDraftPreview({
  runId,
  packId,
  clientName,
  clientContact,
  projectTitle,
  principal,
  currency,
  language,
  lineItems,
  totalAmount,
  missingFields,
}: ProposalDraftPreviewProps) {
  const getServiceLabel = (key: string) => {
    const svc = SERVICE_CATALOG[key]
    if (!svc) return key
    return language === 'vi' ? svc.labelVi : svc.labelEn
  }

  return (
    <AgencyCard variant="glass" className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <FileText className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">02 · Proposal & Rate Preview</h3>
            <p className="text-[11px] text-neutral-500">
              Live calculation matching <code className="text-neutral-300">src/opc/engine.py</code>
            </p>
          </div>
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-mono text-emerald-400">
          {packId}
        </span>
      </div>

      <div className="rounded-xl border border-white/10 bg-[#06080d] p-4 font-mono text-xs space-y-2 mb-4">
        <div className="flex items-center justify-between text-neutral-500 text-[10px]">
          <span>RUN ID · {runId}</span>
          <span>DRAFT · SAMPLE_DATA</span>
        </div>
        <div className="text-emerald-400 font-bold text-sm pt-1">=== PROPOSAL: {projectTitle} ===</div>
        <div className="text-neutral-300">
          Client: {clientName} ({clientContact})
        </div>
        <div className="text-neutral-400">Prepared By: {principal}</div>
        <div className="text-neutral-400">
          Currency: {currency} | Known Total: {formatMoney(totalAmount, currency)}
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
          Line Items ({lineItems.length})
        </div>
        {lineItems.map((item) => (
          <div
            key={item.service}
            className={`flex items-center justify-between rounded-lg border px-3.5 py-2.5 text-xs ${
              item.isUnpriced
                ? 'border-amber-500/40 bg-amber-500/5'
                : 'border-white/5 bg-[#06080d]'
            }`}
          >
            <div>
              <div className="text-white font-medium">{getServiceLabel(item.service)}</div>
              <div className="text-[10px] font-mono text-neutral-500">
                {item.service} · {item.hours}h
              </div>
            </div>
            <div className="text-right font-mono">
              {item.isUnpriced ? (
                <span className="text-amber-400 text-[11px] font-bold">UNPRICED · $0.00 coerced: FALSE</span>
              ) : (
                <>
                  <div className="text-emerald-400 font-bold">{formatMoney(item.subtotal, currency)}</div>
                  <div className="text-[10px] text-neutral-500">@ {formatMoney(item.rate, currency)}/h</div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
        <span className="text-xs text-neutral-400">Known Subtotal ({currency})</span>
        <span className="text-lg font-mono font-extrabold text-white">
          {formatMoney(totalAmount, currency)}
        </span>
      </div>

      {missingFields.length > 0 ? (
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-[11px] text-amber-200 space-y-0.5">
            <div className="font-bold">Unpriced scope flagged for Honest Ledger</div>
            {missingFields.map((m) => (
              <div key={m} className="font-mono text-[10px] text-amber-300/80">
                • {m}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 flex items-center gap-2 text-[11px] text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          All requested services have deterministic rates in the active profile.
        </div>
      )}
    </AgencyCard>
  )
}
