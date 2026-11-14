'use client'

import React from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { Scale, AlertOctagon, CheckCircle2, Cpu, Gauge, ArrowRight } from 'lucide-react'
import {
  PROFILE_4_ROUTING_CHAIN,
  VN_SME_WORKFLOW_TIERS,
  formatCurrencyAmount,
  type OpcUsageEvent,
  type SmeQuotaTierKey,
  type SupportedCurrency,
  type SupportedLanguage,
  type UsageStage,
} from '@/lib/opc-cockpit-data'

interface HonestUsageLedgerProps {
  runId: string
  language: SupportedLanguage
  currency: SupportedCurrency
  selectedTier: SmeQuotaTierKey
  onSelectTier: (tier: SmeQuotaTierKey) => void
  events: OpcUsageEvent[]
  hasUnknownCosts: boolean
  knownTotal: number
}

const STAGE_STYLES: Record<
  UsageStage,
  { labelVi: string; labelEn: string; badge: string }
> = {
  estimated: {
    labelVi: 'DỰ TÍNH',
    labelEn: 'ESTIMATED',
    badge: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  },
  reserved: {
    labelVi: 'GIỮ HẠN MỨC',
    labelEn: 'RESERVED',
    badge: 'border-purple-500/30 bg-purple-500/10 text-purple-300',
  },
  actual: {
    labelVi: 'THỰC TẾ',
    labelEn: 'ACTUAL',
    badge: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  unknown: {
    labelVi: 'CHƯA RÕ GIÁ',
    labelEn: 'UNKNOWN',
    badge: 'border-amber-500/40 bg-amber-500/15 text-amber-300',
  },
}

const TIER_ORDER: SmeQuotaTierKey[] = ['starter', 'pilot_a', 'growth', 'agency']

export default function HonestUsageLedger({
  runId,
  language,
  currency,
  selectedTier,
  onSelectTier,
  events,
  hasUnknownCosts,
  knownTotal,
}: HonestUsageLedgerProps) {
  const isVi = language === 'vi'
  const totalTokens = events.reduce((acc, ev) => acc + ev.tokens, 0)
  const activeTierSpec = VN_SME_WORKFLOW_TIERS[selectedTier]
  const quotaPct = Math.min(
    100,
    Math.round((activeTierSpec.usedSample / activeTierSpec.monthlyQuota) * 100)
  )

  return (
    <AgencyCard variant="glass" className="p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <Scale className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isVi
                ? '04 · Sổ Cái Chi Phí Minh Bạch & Hạn Mức Quy Trình'
                : '04 · Honest Usage Ledger & Profile 4 Routing'}
            </h3>
            <p className="text-[11px] text-neutral-400">
              {isVi
                ? 'Ưu tiên xử lý tất định 0đ; tuyệt đối không tự ép chi phí chưa biết về 0đ.'
                : 'Profile 4 Selective AI routing; never coerces unpriced external costs to zero.'}
            </p>
          </div>
        </div>

        <span
          className={`self-start sm:self-auto rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold ${
            hasUnknownCosts
              ? 'border border-amber-500/50 bg-amber-500/15 text-amber-300'
              : 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
          }`}
        >
          {hasUnknownCosts ? 'UNKNOWN_COST_EVENT · ACTIVE' : 'KNOWN_COST_VERIFIED · 0đ'}
        </span>
      </div>

      {/* Profile 4 Selective AI Routing Chain */}
      <div className="rounded-xl border border-white/10 bg-[#06080d] p-3.5 mb-4 space-y-2.5">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-neutral-400">
          <span className="flex items-center gap-1.5 text-emerald-300 font-bold">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            {isVi
              ? 'Định tuyến AI Chọn lọc Profile 4 (SelectiveRouter)'
              : 'Profile 4 Selective AI Routing Chain'}
          </span>
          <span>1500ms Failover</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {PROFILE_4_ROUTING_CHAIN.map((step, index) => {
            const isActiveStep = index === 0 || (index === 1 && totalTokens > 0)
            return (
              <div
                key={step.id}
                className={`rounded-lg border p-2.5 text-xs relative ${
                  isActiveStep
                    ? 'border-emerald-500/40 bg-emerald-500/10'
                    : 'border-white/10 bg-black/40'
                }`}
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="font-bold text-white text-[11px]">
                    {isVi ? step.titleVi : step.titleEn}
                  </span>
                  {index < PROFILE_4_ROUTING_CHAIN.length - 1 && (
                    <ArrowRight className="hidden sm:block w-3 h-3 text-neutral-500 shrink-0" />
                  )}
                </div>
                <div className="text-[10px] font-mono text-emerald-300 mb-1">
                  {isVi ? step.costBadgeVi : step.costBadgeEn}
                </div>
                <p className="text-[10px] text-neutral-400 leading-snug">
                  {isVi ? step.slaNoteVi : step.slaNoteEn}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* VN SME Monthly Workflow Quota */}
      <div className="rounded-xl border border-white/10 bg-[#06080d] p-3.5 mb-4 space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-emerald-400" />
            {isVi
              ? 'Hạn mức quy trình/tháng (Starter 300 / Pilot A 500 / Growth 1.000 / Agency 3.500)'
              : 'Monthly Workflow Quota (Starter 300 / Pilot A 500 / Growth 1,000 / Agency 3,500)'}
          </span>
          <span className="text-[10px] font-mono text-emerald-300">
            {formatCurrencyAmount(activeTierSpec.monthlyPriceVnd, 'VND')}/{isVi ? 'tháng' : 'mo'}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5" role="group" aria-label="SME Quota Tier">
          {TIER_ORDER.map((tierKey) => {
            const spec = VN_SME_WORKFLOW_TIERS[tierKey]
            const active = selectedTier === tierKey
            return (
              <button
                key={tierKey}
                type="button"
                onClick={() => onSelectTier(tierKey)}
                className={`rounded-lg border px-2.5 py-2 text-left transition-all ${
                  active
                    ? 'border-emerald-500/60 bg-emerald-500/15 text-white'
                    : 'border-white/10 bg-black/40 text-neutral-400 hover:text-white'
                }`}
              >
                <div className="text-[11px] font-bold">{spec.nameVi}</div>
                <div className="text-[10px] font-mono text-emerald-300">
                  {spec.monthlyQuota.toLocaleString('vi-VN')} {isVi ? 'quy trình' : 'runs'}
                </div>
              </button>
            )
          })}
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-neutral-300">
              {isVi ? 'Đã dùng kỳ này (SQLite WAL Lock):' : 'Current Period Used (SQLite WAL):'}{' '}
              <strong className="text-white">
                {activeTierSpec.usedSample.toLocaleString('vi-VN')} /{' '}
                {activeTierSpec.monthlyQuota.toLocaleString('vi-VN')}
              </strong>{' '}
              {isVi ? 'quy trình/tháng' : 'workflows/mo'}
            </span>
            <span className="text-emerald-400 font-bold">{quotaPct}%</span>
          </div>
          <div className="h-2 rounded-full bg-neutral-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all"
              style={{ width: `${quotaPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* KPI Summary Tiles */}
      <div className="grid grid-cols-3 gap-2.5 mb-4">
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-400">
            {isVi ? 'Chi phí AI đã biết' : 'Known AI Cost'}
          </div>
          <div className="text-sm font-mono font-bold text-emerald-400 mt-1">
            {formatCurrencyAmount(knownTotal, currency)}
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-400">
            {isVi ? 'Tổng Token' : 'Total Tokens'}
          </div>
          <div className="text-sm font-mono font-bold text-white mt-1">
            {totalTokens.toLocaleString('vi-VN')}
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#06080d] p-3">
          <div className="text-[10px] font-mono uppercase text-neutral-400">
            {isVi ? 'Bút toán sổ cái' : 'Ledger Events'}
          </div>
          <div className="text-sm font-mono font-bold text-white mt-1">{events.length}</div>
        </div>
      </div>

      {/* Usage Event Rows */}
      <div className="space-y-2">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400">
          opc_usage_events ({runId})
        </div>
        {events.map((ev) => {
          const st = STAGE_STYLES[ev.stage]
          const isUnknownEvent =
            ev.amount === null || ev.stage === 'unknown' || ev.event_code === 'UNKNOWN_COST_EVENT'
          return (
            <div
              key={ev.event_id}
              className={`flex items-center justify-between rounded-lg border px-3.5 py-2.5 text-xs font-mono ${
                isUnknownEvent
                  ? 'border-amber-500/40 bg-amber-500/10'
                  : 'border-white/5 bg-[#06080d]'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className={`rounded px-2 py-0.5 text-[10px] border font-bold shrink-0 ${st.badge}`}>
                  {isVi ? st.labelVi : st.labelEn}
                </span>
                <div className="truncate">
                  <div className="text-white text-xs truncate">
                    {ev.provider} · {ev.model}
                  </div>
                  <div className="text-[10px] text-neutral-400 truncate">
                    {ev.event_id} · {ev.pricing_source} · {ev.tokens} tok
                  </div>
                </div>
              </div>
              <div className="text-right shrink-0 ml-2">
                {isUnknownEvent ? (
                  <span className="text-amber-300 font-bold text-[11px]">
                    UNKNOWN_COST_EVENT (NULL)
                  </span>
                ) : (
                  <span className="text-emerald-400 font-bold">
                    {ev.currency === 'VND' ? `${ev.amount} ₫` : `${ev.amount} ${ev.currency}`}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Explicit Honesty Banner */}
      {hasUnknownCosts ? (
        <div className="mt-4 rounded-xl border border-amber-500/40 bg-amber-500/15 p-3.5 flex items-start gap-2.5 text-[11px] text-amber-100">
          <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-amber-300">
              {isVi
                ? 'Cảnh báo trung thực chi phí (UNKNOWN_COST_EVENT): '
                : 'Honest Cost Invariant Active (UNKNOWN_COST_EVENT): '}
            </span>
            {isVi
              ? 'Phát hiện kết nối bên ngoài chưa có biểu giá cố định. Hệ thống giữ nguyên trạng thái UNKNOWN_COST_EVENT (has_unknown_costs=true), tuyệt đối không tự ghi thành 0đ để tránh sai lệch lãi lỗ.'
              : 'An external connector reported unpriced usage (amount=null). The ledger preserves UNKNOWN_COST_EVENT (has_unknown_costs=true) rather than silently coercing unknown costs to 0.'}
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 flex items-center gap-2 text-[11px] text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          {isVi
            ? '100% bước xử lý chạy qua Tất định Python 0đ & Local MLX — không phát sinh phí ẩn (has_unknown_costs=false).'
            : '100% of workflow stages resolved via Deterministic Python (0 VND) & Local MLX (has_unknown_costs=false).'}
        </div>
      )}
    </AgencyCard>
  )
}
