'use client'

import React, { useMemo, useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  QrCode,
  FileSpreadsheet,
  ShieldCheck,
} from 'lucide-react'
import {
  MIN_EXTRACTION_CONFIDENCE,
  SERVICE_CATALOG,
  buildTvanDraftPreview,
  formatCurrencyAmount,
  type AccountingTargetProvider,
  type OpcLineItem,
  type QuoteFinancialSummary,
  type SupportedCurrency,
  type SupportedLanguage,
  type TvanExportFormat,
} from '@/lib/opc-cockpit-data'

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
  financials: QuoteFinancialSummary
  extractionConfidence: number
  citationCount: number
  missingFields: string[]
}

const EXPORT_FORMATS: TvanExportFormat[] = ['CSV', 'XML', 'JSON']
const ACCOUNTING_PROVIDERS: { key: AccountingTargetProvider; label: string }[] = [
  { key: 'misa_meinvoice', label: 'MISA meInvoice' },
  { key: 'sapo_invoice', label: 'Sapo Invoice' },
]

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
  financials,
  extractionConfidence,
  citationCount,
  missingFields,
}: ProposalDraftPreviewProps) {
  const [exportFormat, setExportFormat] = useState<TvanExportFormat>('JSON')
  const [targetProvider, setTargetProvider] = useState<AccountingTargetProvider>('misa_meinvoice')
  const isVi = language === 'vi'

  const getServiceLabel = (key: string) => {
    const svc = SERVICE_CATALOG[key]
    if (!svc) return key
    return isVi ? svc.labelVi : svc.labelEn
  }

  const isConfidenceOk = extractionConfidence >= MIN_EXTRACTION_CONFIDENCE
  const confidencePct = Math.round(extractionConfidence * 100)

  const draftPreviewText = useMemo(
    () =>
      buildTvanDraftPreview({
        format: exportFormat,
        provider: targetProvider,
        runId,
        buyerName: clientName,
        currency,
        lineItems,
        financials,
        language,
      }),
    [exportFormat, targetProvider, runId, clientName, currency, lineItems, financials, language]
  )

  return (
    <AgencyCard variant="glass" className="p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <FileText className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isVi
                ? '02 · Bản Nháp Báo Giá, VietQR Napas 247 & Nháp Hóa Đơn'
                : '02 · Quote Calculation, VietQR Napas 247 & TVAN Draft'}
            </h3>
            <p className="text-[11px] text-neutral-400">
              {isVi
                ? 'Tính tiền chính xác từng đồng (không sai số làm tròn), gán mã VietQR riêng theo đơn.'
                : 'Decimal-exact line item + VAT math, single-order VietQR memo & pre-accounting draft.'}
            </p>
          </div>
        </div>
        <span className="self-start sm:self-auto rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-mono text-emerald-400">
          {packId}
        </span>
      </div>

      {/* Confidence / Handoff Gate Banner */}
      {!isConfidenceOk && (
        <div className="mb-4 rounded-xl border border-amber-500/50 bg-amber-500/15 p-3.5 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-100 space-y-1">
            <div className="font-bold text-amber-300">
              Chuyển nhân viên chat tay trên Zalo OA Manager / HANDOFF_ZALO_OA_MANAGER
            </div>
            <p className="text-[11px] text-amber-200/90">
              {isVi
                ? `Độ tin cậy trích xuất hiện tại là ${confidencePct}% (< 85%). Hệ thống tự động chặn gửi báo giá tự động để nhân viên kiểm tra trực tiếp với khách trên Zalo OA Manager.`
                : `Extraction confidence is ${confidencePct}% (< 85%). Auto-send is paused so your team can reply manually in Zalo OA Manager.`}
            </p>
          </div>
        </div>
      )}

      {/* Quote Header Summary */}
      <div className="rounded-xl border border-white/10 bg-[#06080d] p-4 font-mono text-xs space-y-1.5 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-neutral-500 text-[10px]">
          <span>RUN ID · {runId}</span>
          <span>
            {isVi ? `TRÍCH DẪN NGUỒN: ${citationCount} VỊ TRÍ` : `CITATIONS: ${citationCount} SPANS`} ·{' '}
            {confidencePct}%
          </span>
        </div>
        <div className="text-emerald-400 font-bold text-sm pt-1">
          {isVi ? `BÁO GIÁ NHÁP: ${projectTitle}` : `PROPOSAL DRAFT: ${projectTitle}`}
        </div>
        <div className="text-neutral-300">
          {isVi ? 'Khách hàng' : 'Client'}: {clientName} ({clientContact})
        </div>
        <div className="text-neutral-400">
          {isVi ? 'Người lập' : 'Prepared By'}: {principal}
        </div>
      </div>

      {/* Line Items */}
      <div className="space-y-2">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400">
          {isVi ? `Chi tiết hạng mục (${lineItems.length})` : `Line Items (${lineItems.length})`}
        </div>
        {lineItems.map((item) => (
          <div
            key={item.service}
            className={`flex items-center justify-between gap-3 rounded-lg border px-3.5 py-2.5 text-xs ${
              item.isUnpriced
                ? 'border-amber-500/40 bg-amber-500/10'
                : 'border-white/5 bg-[#06080d]'
            }`}
          >
            <div className="min-w-0">
              <div className="text-white font-medium truncate">{getServiceLabel(item.service)}</div>
              <div className="text-[10px] font-mono text-neutral-400">
                {item.service} · {item.hours} {isVi ? 'giờ/đơn vị' : 'hrs'}
              </div>
            </div>
            <div className="text-right font-mono shrink-0">
              {item.isUnpriced ? (
                <span className="text-amber-300 text-[11px] font-bold">
                  {isVi ? 'CHƯA ĐỊNH GIÁ · Không ép về 0đ' : 'UNPRICED · Never coerced to 0'}
                </span>
              ) : (
                <>
                  <div className="text-emerald-400 font-bold">
                    {formatCurrencyAmount(item.subtotal, currency)}
                  </div>
                  <div className="text-[10px] text-neutral-400">
                    @ {formatCurrencyAmount(item.rate, currency)}/{isVi ? 'đv' : 'h'}
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Subtotal + VAT + Grand Total */}
      <div className="mt-4 pt-3 border-t border-white/10 space-y-1.5 text-xs">
        <div className="flex items-center justify-between text-neutral-400">
          <span>{isVi ? `Tạm tính trước thuế (${currency})` : `Subtotal before VAT (${currency})`}</span>
          <span className="font-mono text-neutral-200">
            {formatCurrencyAmount(financials.subtotal, currency)}
          </span>
        </div>
        <div className="flex items-center justify-between text-neutral-400">
          <span>
            {isVi
              ? `Thuế GTGT (VAT ${financials.vatRatePct}%)`
              : `Value-Added Tax (VAT ${financials.vatRatePct}%)`}
          </span>
          <span className="font-mono text-neutral-200">
            {formatCurrencyAmount(financials.vatAmount, currency)}
          </span>
        </div>
        <div className="flex items-center justify-between pt-1.5 border-t border-white/5">
          <span className="font-bold text-white">
            {isVi ? `Tổng thanh toán (${currency})` : `Grand Total (${currency})`}
          </span>
          <span className="text-lg font-mono font-extrabold text-emerald-400">
            {formatCurrencyAmount(financials.grandTotal, currency)}
          </span>
        </div>
      </div>

      {/* VietQR Napas 247 Single-Order Binding Box */}
      <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3.5 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-300">
            <QrCode className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {isVi
                ? 'Thanh toán chuyển khoản nhanh VietQR Napas 247'
                : 'VietQR Napas 247 Instant Bank Transfer'}
            </span>
          </div>
          <span className="rounded bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-mono text-emerald-300">
            EMVCo Dynamic QR
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
          <div className="rounded-lg bg-black/40 border border-white/5 p-2.5">
            <div className="text-[10px] text-neutral-400">
              {isVi ? 'SỐ TIỀN QUÉT QR (VND)' : 'VIETQR AMOUNT (VND)'}
            </div>
            <div className="text-sm font-bold text-white mt-0.5">
              {formatCurrencyAmount(financials.vietQrAmountVnd, 'VND')}
            </div>
          </div>
          <div className="rounded-lg bg-black/40 border border-white/5 p-2.5">
            <div className="text-[10px] text-neutral-400">
              {isVi ? 'NỘI DUNG CHUYỂN KHOẢN KHÓA ĐƠN' : 'SINGLE-ORDER MEMO BINDING'}
            </div>
            <div className="text-sm font-bold text-emerald-300 mt-0.5 select-all">
              {financials.vietQrMemo}
            </div>
          </div>
        </div>

        <div className="text-[11px] text-neutral-300">
          {financials.vietQrAccountLabel}
        </div>
        <div className="rounded-lg bg-black/50 border border-white/5 px-2.5 py-1.5 text-[10px] font-mono text-neutral-400 truncate select-all">
          EMVCo: {financials.vietQrEmvcoPreview}
        </div>
      </div>

      {/* Statutory Accounting Draft Badge & Export Format Selector */}
      <div className="mt-4 rounded-xl border border-blue-500/30 bg-blue-500/5 p-3.5 space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-500/15 px-2.5 py-1 text-[10px] font-mono font-bold text-amber-200">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-300 shrink-0" />
            NHÁP CHỜ KÝ SỐ TVAN (DRAFT_PENDING_TVAN — MISA / Sapo)
          </span>

          <div className="flex items-center gap-1" role="group" aria-label="Export Format">
            {EXPORT_FORMATS.map((fmt) => (
              <button
                key={fmt}
                type="button"
                onClick={() => setExportFormat(fmt)}
                className={`rounded-md px-2.5 py-1 text-[10px] font-mono font-bold border transition-colors ${
                  exportFormat === fmt
                    ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-300'
                    : 'border-white/10 bg-[#06080d] text-neutral-400 hover:text-white'
                }`}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
          <span className="text-neutral-300 flex items-center gap-1.5">
            <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            {isVi
              ? ' Chuẩn Nghị định 123 & TT78: Chỉ xuất dữ liệu nháp cho kế toán ký số trên MISA/Sapo.'
              : ' Decree 123 & Circular 78 compliant: Exports pre-accounting draft for TVAN signing only.'}
          </span>
          <div className="flex gap-1.5">
            {ACCOUNTING_PROVIDERS.map((p) => (
              <button
                key={p.key}
                type="button"
                onClick={() => setTargetProvider(p.key)}
                className={`rounded px-2 py-0.5 text-[10px] font-mono border transition-colors ${
                  targetProvider === p.key
                    ? 'border-blue-400/50 bg-blue-500/20 text-blue-200 font-bold'
                    : 'border-white/10 text-neutral-400 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <pre className="max-h-36 overflow-auto rounded-lg border border-white/10 bg-[#06080d] p-2.5 text-[10px] font-mono text-neutral-300 leading-relaxed">
          {draftPreviewText}
        </pre>
      </div>

      {/* Missing / Unpriced Honesty Notice */}
      {missingFields.length > 0 ? (
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-[11px] text-amber-200 space-y-0.5">
            <div className="font-bold">
              {isVi
                ? 'Có hạng mục chưa có đơn giá — đã chuyển sang Sổ cái Chi phí Minh bạch'
                : 'Unpriced scope flagged for Honest Usage Ledger'}
            </div>
            {missingFields.map((m) => (
              <div key={m} className="font-mono text-[10px] text-amber-300/90">
                • {m}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 flex items-center gap-2 text-[11px] text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          {isVi
            ? 'Tất cả hạng mục trong báo giá đều có đơn giá niêm yết rõ ràng.'
            : 'All requested services have deterministic rates in the active catalog.'}
        </div>
      )}
    </AgencyCard>
  )
}
