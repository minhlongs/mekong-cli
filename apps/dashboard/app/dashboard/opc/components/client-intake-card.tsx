'use client'

import React, { useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import {
  Globe2,
  Clock,
  User,
  Briefcase,
  MessageSquareQuote,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
} from 'lucide-react'
import {
  MIN_EXTRACTION_CONFIDENCE,
  SERVICE_CATALOG,
  ZALO_FREE_WINDOW_HOURS,
  formatCurrencyAmount,
  type SourceSpanCitation,
  type SupportedCurrency,
  type SupportedLanguage,
  type VatRatePct,
} from '@/lib/opc-cockpit-data'

export interface ClientIntake {
  requestId: string
  clientName: string
  clientContact: string
  projectTitle: string
  inboundMessage: string
  zaloInteractionAgeHours: number
  extractionConfidence: number
  vatRatePct: VatRatePct
  estimatedHours: number
  currency: SupportedCurrency
  timezone: string
  language: SupportedLanguage
  services: string[]
  attachments: string[]
  principal: string
}

const CURRENCIES: SupportedCurrency[] = ['VND', 'USD', 'EUR']
const VAT_RATES: VatRatePct[] = [8, 10, 0]

const TIMEZONES = [
  'Asia/Ho_Chi_Minh',
  'Asia/Singapore',
  'Asia/Bangkok',
  'UTC',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
]

interface ClientIntakeCardProps {
  value: ClientIntake
  citations: SourceSpanCitation[]
  onChange: (next: ClientIntake) => void
}

const labelStyle =
  'text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-400 mb-1.5 block'
const inputStyle =
  'w-full rounded-xl border border-white/10 bg-[#06080d] px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-emerald-500/50 focus:outline-none transition-colors'

export default function ClientIntakeCard({
  value,
  citations,
  onChange,
}: ClientIntakeCardProps) {
  const [attachmentDraft, setAttachmentDraft] = useState('')
  const isVi = value.language === 'vi'

  const update = <K extends keyof ClientIntake>(key: K, next: ClientIntake[K]) => {
    onChange({ ...value, [key]: next })
  }

  const toggleService = (service: string) => {
    const has = value.services.includes(service)
    onChange({
      ...value,
      services: has ? value.services.filter((s) => s !== service) : [...value.services, service],
    })
  }

  const addAttachment = () => {
    const trimmed = attachmentDraft.trim()
    if (!trimmed || value.attachments.includes(trimmed)) return
    onChange({ ...value, attachments: [...value.attachments, trimmed] })
    setAttachmentDraft('')
  }

  const confidencePct = Math.round(value.extractionConfidence * 100)
  const isConfidenceVerified = value.extractionConfidence >= MIN_EXTRACTION_CONFIDENCE
  const isZaloWindowValid =
    value.zaloInteractionAgeHours >= 0 && value.zaloInteractionAgeHours <= ZALO_FREE_WINDOW_HOURS
  const remainingWindowHours = Math.max(0, ZALO_FREE_WINDOW_HOURS - value.zaloInteractionAgeHours)

  return (
    <AgencyCard variant="glass" className="p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <MessageSquareQuote className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isVi
                ? '01 · Tiếp nhận Tin nhắn Khách từ Zalo OA'
                : '01 · Zalo OA Lead Intake & Source Citations'}
            </h3>
            <p className="text-[11px] text-neutral-400">
              {isVi
                ? 'Tự động bóc tách yêu cầu báo giá, kiểm tra khung 48h Zalo OA & trích dẫn vị trí câu chữ gốc.'
                : 'Extracts quote scope with character-level source_span provenance & 48h Zalo OA window check.'}
            </p>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] font-mono font-bold shrink-0 ${
            isZaloWindowValid
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              : 'border-red-500/40 bg-red-500/15 text-red-300'
          }`}
        >
          <Clock className="w-3 h-3" />
          {isZaloWindowValid
            ? isVi
              ? `Zalo OA 48h: Còn ${remainingWindowHours}h miễn phí`
              : `Zalo OA 48h Free Window: ${remainingWindowHours}h left`
            : isVi
            ? `Quá hạn 48h Zalo (${value.zaloInteractionAgeHours}h)`
            : `Zalo 48h Expired (${value.zaloInteractionAgeHours}h)`}
        </span>
      </div>

      {/* Inbound Zalo Message + Confidence + Source Spans */}
      <div className="rounded-xl border border-white/10 bg-[#06080d] p-4 mb-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label htmlFor="opc-zalo-message" className="text-[11px] font-mono font-bold uppercase text-emerald-400">
            {isVi ? 'Tin nhắn khách gửi trên Zalo OA' : 'Customer Inbound Zalo OA Message'}
          </label>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => update('extractionConfidence', 0.94)}
              className={`rounded-md px-2 py-1 text-[10px] font-mono border transition-colors ${
                isConfidenceVerified
                  ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300 font-bold'
                  : 'border-white/10 text-neutral-400 hover:text-white'
              }`}
            >
              {isVi ? 'Mẫu chuẩn (94%)' : 'High Conf (94%)'}
            </button>
            <button
              type="button"
              onClick={() => update('extractionConfidence', 0.72)}
              className={`rounded-md px-2 py-1 text-[10px] font-mono border transition-colors ${
                !isConfidenceVerified
                  ? 'border-amber-500/50 bg-amber-500/15 text-amber-300 font-bold'
                  : 'border-white/10 text-neutral-400 hover:text-white'
              }`}
            >
              {isVi ? 'Thử <85% (72%)' : 'Test <85% (72%)'}
            </button>
          </div>
        </div>

        <textarea
          id="opc-zalo-message"
          rows={3}
          className={`${inputStyle} text-xs leading-relaxed`}
          value={value.inboundMessage}
          onChange={(e) => update('inboundMessage', e.target.value)}
          placeholder={
            isVi
              ? 'Nhập nội dung tin nhắn khách hỏi giá qua Zalo OA...'
              : 'Paste inbound Zalo OA customer inquiry...'
          }
        />

        {/* Confidence Status Bar */}
        <div
          className={`rounded-lg border px-3 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs ${
            isConfidenceVerified
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
              : 'border-amber-500/40 bg-amber-500/15 text-amber-200'
          }`}
        >
          <div className="flex items-start sm:items-center gap-2">
            {isConfidenceVerified ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5 sm:mt-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5 sm:mt-0" />
            )}
            <div>
              <span className="font-bold">
                {isVi ? `Độ tin cậy bóc tách: ${confidencePct}%` : `Extraction Confidence: ${confidencePct}%`}
              </span>
              <span className="block sm:inline sm:ml-2 text-[11px] opacity-90">
                {isConfidenceVerified
                  ? isVi
                    ? '(>= 85% · Đạt chuẩn tự động lập báo giá nháp)'
                    : '(>= 85% · Verified for automated draft quote)'
                  : isVi
                  ? '(< 85% · Chuyển nhân viên chat tay trên Zalo OA Manager / HANDOFF_ZALO_OA_MANAGER)'
                  : '(< 85% · Route to human agent / HANDOFF_ZALO_OA_MANAGER)'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <label htmlFor="opc-confidence-range" className="sr-only">
              {isVi ? 'Điều chỉnh độ tin cậy' : 'Adjust extraction confidence'}
            </label>
            <input
              id="opc-confidence-range"
              type="range"
              min={50}
              max={100}
              value={confidencePct}
              onChange={(e) => update('extractionConfidence', Number(e.target.value) / 100)}
              className="w-24 accent-emerald-500 cursor-pointer"
            />
          </div>
        </div>

        {/* Field-Level source_span Citations */}
        <div className="pt-1 space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-neutral-400">
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-emerald-400" />
              {isVi
                ? `Trích dẫn câu gốc (source_span · ${citations.length} trường khớp)`
                : `Field-Level Source Citations (source_span · ${citations.length} matched)`}
            </span>
            <span>[start..end]</span>
          </div>

          {citations.length > 0 ? (
            <div className="grid grid-cols-1 gap-1.5">
              {citations.map((span) => (
                <div
                  key={span.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 rounded-lg border border-white/10 bg-black/50 px-3 py-2 text-[11px]"
                >
                  <div className="min-w-0">
                    <span className="text-neutral-300 font-medium">
                      {isVi ? span.labelVi : span.labelEn}:
                    </span>{' '}
                    <span className="text-emerald-300 font-mono">
                      &ldquo;{span.matchedText}&rdquo;
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 font-mono text-[10px]">
                    <span className="rounded bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.5 text-emerald-300">
                      source_span [{span.start}..{span.end}]
                    </span>
                    <span className="text-neutral-400">→ {span.resolvedValue}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200">
              {isVi
                ? 'Chưa tìm thấy cụm từ khớp trực tiếp trong tin nhắn — khuyến nghị kiểm tra tay trước khi duyệt.'
                : 'No exact substring citations matched in inbound text — verify line items manually.'}
            </div>
          )}
        </div>
      </div>

      {/* Structured Intake Fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="opc-principal" className={labelStyle}>
            {isVi ? 'Chủ doanh nghiệp / Người duyệt' : 'Business Owner (Principal)'}
          </label>
          <div className="relative">
            <User className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-500" />
            <input
              id="opc-principal"
              className={`${inputStyle} pl-9`}
              value={value.principal}
              onChange={(e) => update('principal', e.target.value)}
              placeholder={isVi ? 'Tên chủ shop / CEO' : 'Owner name'}
            />
          </div>
        </div>

        <div>
          <label htmlFor="opc-client-name" className={labelStyle}>
            {isVi ? 'Tên khách hàng / Công ty mua' : 'Customer / Buyer Entity'}
          </label>
          <input
            id="opc-client-name"
            className={inputStyle}
            value={value.clientName}
            onChange={(e) => update('clientName', e.target.value)}
            placeholder={isVi ? 'Công ty TNHH...' : 'Client legal entity'}
          />
        </div>

        <div>
          <label htmlFor="opc-client-contact" className={labelStyle}>
            {isVi ? 'Mã Zalo khách / Liên hệ nhận báo giá' : 'Zalo Recipient / Contact'}
          </label>
          <input
            id="opc-client-contact"
            className={inputStyle}
            value={value.clientContact}
            onChange={(e) => update('clientContact', e.target.value)}
            placeholder="zalo:84909123456"
          />
        </div>

        <div>
          <label htmlFor="opc-project-title" className={labelStyle}>
            {isVi ? 'Tên gói dịch vụ / Đơn hàng' : 'Quote / Order Title'}
          </label>
          <input
            id="opc-project-title"
            className={inputStyle}
            value={value.projectTitle}
            onChange={(e) => update('projectTitle', e.target.value)}
            placeholder={isVi ? 'Gói dịch vụ báo giá' : 'Scope of work'}
          />
        </div>

        <div>
          <label htmlFor="opc-hours" className={labelStyle}>
            {isVi ? 'Tổng khối lượng (Giờ / Đơn vị)' : 'Total Effort (Hours / Units)'}
          </label>
          <input
            id="opc-hours"
            type="number"
            min={1}
            className={inputStyle}
            value={value.estimatedHours}
            onChange={(e) => update('estimatedHours', Math.max(1, Number(e.target.value) || 1))}
          />
        </div>

        <div>
          <label className={labelStyle}>{isVi ? 'Loại tiền & Thuế GTGT (VAT)' : 'Currency & VAT Rate'}</label>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex gap-1" role="group" aria-label="Currency">
              {CURRENCIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => update('currency', c)}
                  className={`flex-1 rounded-lg border py-2 text-xs font-mono font-bold transition-all ${
                    value.currency === c
                      ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-300'
                      : 'border-white/10 bg-[#06080d] text-neutral-400 hover:text-white'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <div className="flex gap-1" role="group" aria-label="VAT Rate">
              {VAT_RATES.map((rate) => (
                <button
                  key={rate}
                  type="button"
                  onClick={() => update('vatRatePct', rate)}
                  className={`flex-1 rounded-lg border py-2 text-xs font-mono font-bold transition-all ${
                    value.vatRatePct === rate
                      ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-300'
                      : 'border-white/10 bg-[#06080d] text-neutral-400 hover:text-white'
                  }`}
                >
                  {rate}%
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <label htmlFor="opc-timezone" className={labelStyle}>
            {isVi ? 'Múi giờ vận hành' : 'IANA Timezone'}
          </label>
          <div className="relative">
            <Clock className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-500" />
            <select
              id="opc-timezone"
              className={`${inputStyle} pl-9`}
              value={value.timezone}
              onChange={(e) => update('timezone', e.target.value)}
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="opc-zalo-age" className={labelStyle}>
            {isVi
              ? 'Thời gian từ tin nhắn cuối của khách (Giờ)'
              : 'Hours Since Last Customer Zalo Message'}
          </label>
          <input
            id="opc-zalo-age"
            type="number"
            min={0}
            max={72}
            className={inputStyle}
            value={value.zaloInteractionAgeHours}
            onChange={(e) =>
              update('zaloInteractionAgeHours', Math.max(0, Number(e.target.value) || 0))
            }
          />
        </div>
      </div>

      {/* Service Catalog */}
      <div className="mt-5">
        <label className={labelStyle}>
          {isVi
            ? 'Danh mục Hạng mục Báo giá (Giá cố định & Minh bạch mục chưa có giá)'
            : 'Service Catalog (Deterministic Rates & Honest Unpriced Flag)'}
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Object.entries(SERVICE_CATALOG).map(([serviceKey, svc]) => {
            const isActive = value.services.includes(serviceKey)
            const rate = svc.rates[value.currency]
            return (
              <button
                key={serviceKey}
                type="button"
                onClick={() => toggleService(serviceKey)}
                className={`flex items-center justify-between gap-2.5 rounded-lg border px-3.5 py-2.5 text-left transition-all min-h-[44px] ${
                  isActive
                    ? 'border-emerald-500/60 bg-emerald-500/10'
                    : 'border-white/10 bg-[#06080d] hover:border-white/20'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Briefcase
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isActive ? 'text-emerald-400' : 'text-neutral-500'
                    }`}
                  />
                  <span
                    className={`text-xs truncate ${
                      isActive ? 'text-white font-medium' : 'text-neutral-300'
                    }`}
                  >
                    {isVi ? svc.labelVi : svc.labelEn}
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono shrink-0 ${
                    rate === null ? 'text-amber-400 font-bold' : 'text-neutral-400'
                  }`}
                >
                  {rate === null
                    ? isVi
                      ? 'CHƯA CÓ GIÁ'
                      : 'UNKNOWN'
                    : formatCurrencyAmount(rate, value.currency)}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Attachments */}
      <div className="mt-5">
        <label htmlFor="opc-attachment-input" className={labelStyle}>
          {isVi ? 'Tệp đính kèm gửi kèm báo giá' : 'Quote Attachments'}
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Globe2 className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-500" />
            <input
              id="opc-attachment-input"
              className={`${inputStyle} pl-9`}
              value={attachmentDraft}
              onChange={(e) => setAttachmentDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addAttachment()
                }
              }}
              placeholder={isVi ? 'bang_gia_dich_vu_2026.pdf' : 'quote_schedule_v1.pdf'}
            />
          </div>
          <button
            type="button"
            onClick={addAttachment}
            className="rounded-lg border border-white/10 bg-[#06080d] px-4 text-xs font-bold text-neutral-300 hover:text-white hover:border-white/30 transition-colors min-h-[42px]"
          >
            {isVi ? 'Thêm tệp' : 'Add'}
          </button>
        </div>
        {value.attachments.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {value.attachments.map((a) => (
              <span
                key={a}
                className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-mono text-neutral-300"
              >
                {a}
                <button
                  type="button"
                  aria-label={isVi ? `Xóa tệp ${a}` : `Remove ${a}`}
                  onClick={() =>
                    onChange({ ...value, attachments: value.attachments.filter((x) => x !== a) })
                  }
                  className="text-neutral-400 hover:text-red-400 font-bold"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </AgencyCard>
  )
}
