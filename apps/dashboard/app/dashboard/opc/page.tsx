'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { ShieldCheck, Terminal, Languages, RefreshCw } from 'lucide-react'
import ClientIntakeCard, { type ClientIntake } from './components/client-intake-card'
import ProposalDraftPreview from './components/proposal-draft-preview'
import CryptographicApprovalCard, {
  type ApprovalState,
  type DispatchOutcome,
} from './components/cryptographic-approval-card'
import HonestUsageLedger from './components/honest-usage-ledger'
import {
  SERVICE_CATALOG,
  ZALO_FREE_WINDOW_HOURS,
  canonicalizePayload,
  computeQuoteFinancials,
  computeSha256Hex,
  extractSourceSpansFromMessage,
  formatActionAmountString,
  formatCurrencyAmount,
  syncPilotADecision,
  syncPilotAZaloWebhook,
  type GatewaySyncResult,
  type OpcActionPayload,
  type OpcLineItem,
  type OpcUsageEvent,
  type SmeQuotaTierKey,
  type SupportedLanguage,
} from '@/lib/opc-cockpit-data'

// Baseline UTC epoch for SSR hydration stability; refreshed to live +24h TTL on client mount.
const SSR_INITIAL_EXPIRES_AT = 1794787200

const INITIAL_INTAKE: ClientIntake = {
  requestId: 'req_zalo_vn_2026_157',
  clientName: 'Công ty TNHH Nội Thất Minh Long',
  clientContact: 'zalo:84909382910',
  projectTitle: 'Triển khai Báo giá Tự động Zalo OA & Đối soát VietQR',
  inboundMessage:
    'Chào shop, bên mình cần gói Zalo OA báo giá tự động kèm đối soát VietQR Napas 247 và xuất hóa đơn VAT 8% trên MISA cho khoảng 12 giờ triển khai trong tuần này.',
  zaloInteractionAgeHours: 6,
  extractionConfidence: 0.94,
  vatRatePct: 8,
  estimatedHours: 12,
  currency: 'VND',
  timezone: 'Asia/Ho_Chi_Minh',
  language: 'vi',
  services: ['zalo_oa_lead_to_quote', 'vietqr_reconciliation_setup', 'misa_sapo_tvan_draft'],
  attachments: ['bang_gia_pilot_a_2026.pdf'],
  principal: 'Nguyễn Minh Tâm (Giám đốc)',
}

export default function OpcCockpitPage() {
  const [intake, setIntake] = useState<ClientIntake>(INITIAL_INTAKE)
  const [expiresAt, setExpiresAt] = useState<number>(SSR_INITIAL_EXPIRES_AT)
  const [runId, setRunId] = useState<string>('run_pilot_a_8f3a91c2b4e0')
  const [selectedTier, setSelectedTier] = useState<SmeQuotaTierKey>('pilot_a')
  const [actionDigest, setActionDigest] = useState<string>('')
  const [boundDigest, setBoundDigest] = useState<string>('')
  const [approvalState, setApprovalState] = useState<ApprovalState>('idle')
  const [isSyncing, setIsSyncing] = useState<boolean>(false)
  const [gatewaySync, setGatewaySync] = useState<GatewaySyncResult>({
    synced: false,
    endpoint: '/v1/opc/pilot-a/webhook/zalo',
    mode: 'offline_webcrypto',
    detail: 'offline_ready',
  })
  const [dispatchResult, setDispatchResult] = useState<DispatchOutcome>({
    status: 'idle',
    message: '',
  })

  const packId = 'vn-sme-ops'
  const isVi = intake.language === 'vi'

  useEffect(() => {
    setExpiresAt(Math.floor(Date.now() / 1000) + 86400)
  }, [])

  const setLanguage = (lang: SupportedLanguage) => {
    setIntake((prev) => ({ ...prev, language: lang }))
  }

  const { lineItems, missingFields } = useMemo(() => {
    const items: OpcLineItem[] = []
    const missing: string[] = []
    const svcCount = Math.max(1, intake.services.length)
    const hoursPerSvc = Math.max(1, Math.floor(intake.estimatedHours / svcCount))

    for (const svcKey of intake.services) {
      const def = SERVICE_CATALOG[svcKey]
      const rate = def ? def.rates[intake.currency] : null
      if (rate === null || rate === undefined) {
        missing.push(
          isVi
            ? `Hạng mục chưa có đơn giá cố định: '${svcKey}'`
            : `Unpriced service: '${svcKey}'`
        )
        items.push({
          service: svcKey,
          hours: hoursPerSvc,
          rate: 0,
          subtotal: 0,
          isUnpriced: true,
        })
      } else {
        const sub = rate * hoursPerSvc
        items.push({
          service: svcKey,
          hours: hoursPerSvc,
          rate,
          subtotal: sub,
          isUnpriced: false,
        })
      }
    }
    return { lineItems: items, missingFields: missing }
  }, [intake.services, intake.estimatedHours, intake.currency, isVi])

  const financials = useMemo(
    () => computeQuoteFinancials(lineItems, intake.currency, intake.vatRatePct, runId),
    [lineItems, intake.currency, intake.vatRatePct, runId]
  )

  const citations = useMemo(
    () =>
      extractSourceSpansFromMessage(
        intake.inboundMessage,
        intake.services,
        intake.estimatedHours,
        intake.vatRatePct
      ),
    [intake.inboundMessage, intake.services, intake.estimatedHours, intake.vatRatePct]
  )

  const actionPayload: OpcActionPayload = useMemo(
    () => ({
      attachments: intake.attachments,
      budget_amount: '0',
      budget_currency: intake.currency,
      capability: 'vn.zalo_oa_followup',
      connector: 'zalo_oa_sandbox',
      content: `[BÁO GIÁ PILOT A] ${intake.projectTitle} · Tổng TT: ${formatCurrencyAmount(
        financials.grandTotal,
        intake.currency
      )} · CK: ${financials.vietQrMemo}`,
      expires_at: expiresAt,
      parameters: {
        amount: formatActionAmountString(financials.grandTotal, intake.currency),
        project_title: intake.projectTitle,
      },
      principal: intake.principal,
      recipient: intake.clientContact,
    }),
    [intake, financials.grandTotal, financials.vietQrMemo, expiresAt]
  )

  useEffect(() => {
    let active = true
    const canonical = canonicalizePayload(actionPayload)
    void computeSha256Hex(canonical).then((hex) => {
      if (active) {
        setActionDigest(hex)
      }
    })
    return () => {
      active = false
    }
  }, [actionPayload])

  const hasUnknownCosts = missingFields.length > 0
  const isZaloWindowValid =
    intake.zaloInteractionAgeHours >= 0 &&
    intake.zaloInteractionAgeHours <= ZALO_FREE_WINDOW_HOURS

  const usageEvents: OpcUsageEvent[] = useMemo(() => {
    const zeroStr = intake.currency === 'VND' ? '0' : '0.00'
    const base: OpcUsageEvent[] = [
      {
        event_id: 'use_det_001',
        run_id: runId,
        stage: 'actual',
        provider: 'deterministic_python_0d',
        model: 'decimal_quote_vietqr_v6',
        tokens: 0,
        amount: zeroStr,
        currency: intake.currency,
        pricing_source: 'local_deterministic_0d',
        routing_tier: 'deterministic_python',
        event_code: 'KNOWN_ZERO_COST',
      },
      {
        event_id: 'use_res_002',
        run_id: runId,
        stage: 'reserved',
        provider: 'sqlite_wal_quota_guard',
        model: `tier_${selectedTier}`,
        tokens: 0,
        amount: zeroStr,
        currency: intake.currency,
        pricing_source: 'workflow_slot_lock',
        routing_tier: 'deterministic_python',
        event_code: 'KNOWN_ZERO_COST',
      },
      {
        event_id: 'use_mlx_003',
        run_id: runId,
        stage: 'actual',
        provider: 'selective_router_local_mlx',
        model: 'qwen2.5-7b-vn-spans',
        tokens: 164,
        amount: zeroStr,
        currency: intake.currency,
        pricing_source: 'on_prem_mlx_0d',
        routing_tier: 'local_mlx',
        event_code: 'KNOWN_ZERO_COST',
      },
    ]

    if (hasUnknownCosts) {
      base.push({
        event_id: 'use_unk_004',
        run_id: runId,
        stage: 'unknown',
        provider: 'custom_connector_bespoke',
        model: 'UNKNOWN_COST_EVENT',
        tokens: 312,
        amount: null,
        currency: intake.currency,
        pricing_source: 'unpriced_external',
        routing_tier: 'cloud_fallback',
        event_code: 'UNKNOWN_COST_EVENT',
      })
    }
    return base
  }, [intake.currency, runId, selectedTier, hasUnknownCosts])

  const handleGatewayWebhookSync = async () => {
    setIsSyncing(true)
    const syncRes = await syncPilotAZaloWebhook({
      eventId: intake.requestId,
      senderName: intake.clientName,
      senderContact: intake.clientContact,
      messageText: intake.inboundMessage,
      projectTitle: intake.projectTitle,
      requestedServices: intake.services,
      estimatedHours: intake.estimatedHours,
      currency: intake.currency,
      language: intake.language,
      extractionConfidence: intake.extractionConfidence,
    })
    setGatewaySync(syncRes)
    if (syncRes.serverRunId) {
      setRunId(syncRes.serverRunId)
    }
    setIsSyncing(false)
  }

  const handleApproveAndSend = async (revisionNotes: string) => {
    if (approvalState === 'consumed') {
      setDispatchResult({
        status: 'consumed',
        message: isVi
          ? 'ApprovalSecurityError: Phiếu duyệt này đã được sử dụng 1 lần — hệ thống tự động chặn gửi trùng báo giá cho khách.'
          : 'ApprovalSecurityError: Token already consumed (single-use replay guard).',
      })
      return
    }

    if (boundDigest && boundDigest !== actionDigest) {
      setDispatchResult({
        status: 'tamper_detected',
        message: isVi
          ? `Phát hiện dữ liệu báo giá bị thay đổi sau khi ký! Mã gốc ${boundDigest.slice(
              0,
              16
            )}… khác mã hiện tại ${actionDigest.slice(0, 16)}…. Đã khóa lệnh gửi!`
          : `Payload mutated after signing! Bound ${boundDigest.slice(
              0,
              16
            )}… != current ${actionDigest.slice(0, 16)}…. Dispatch aborted!`,
      })
      return
    }

    const lockedDigest = actionDigest
    setBoundDigest(lockedDigest)
    setApprovalState('approved')
    setIsSyncing(true)

    const syncRes = await syncPilotADecision({
      runId,
      decision: 'approve',
      actionDigest: lockedDigest,
      revisionNotes,
    })
    setGatewaySync(syncRes)
    setIsSyncing(false)
    setApprovalState('consumed')

    const syncTag =
      syncRes.mode === 'live_gateway'
        ? isVi
          ? 'Đã đồng bộ FastAPI Gateway trực tiếp'
          : 'Synced via live FastAPI Gateway'
        : isVi
        ? 'Xác thực Web Crypto nội bộ (Offline-safe)'
        : 'Verified via local Web Crypto (Offline-safe)'

    setDispatchResult({
      status: 'success',
      message: isVi
        ? `Đã gửi báo giá & mã VietQR (${financials.vietQrMemo}) tới ${actionPayload.recipient}. Khóa chống gửi trùng: idem_${lockedDigest.slice(
            0,
            12
          )} · ${syncTag}.`
        : `Dispatched quote & VietQR (${financials.vietQrMemo}) to ${actionPayload.recipient} (key: idem_${lockedDigest.slice(
            0,
            12
          )}) · ${syncTag}.`,
    })
  }

  const handleHandoffZalo = async (revisionNotes: string) => {
    setIsSyncing(true)
    const syncRes = await syncPilotADecision({
      runId,
      decision: 'handoff',
      actionDigest,
      revisionNotes,
    })
    setGatewaySync(syncRes)
    setIsSyncing(false)
    setApprovalState('revoked')
    setDispatchResult({
      status: 'revoked',
      message: isVi
        ? `HANDOFF_ZALO_OA_MANAGER: Đã dừng gửi tự động và chuyển hội thoại của ${intake.clientName} sang nhân viên trực trên Zalo OA Manager.`
        : `HANDOFF_ZALO_OA_MANAGER: Auto-send halted; conversation for ${intake.clientName} routed to human operator in Zalo OA Manager.`,
    })
  }

  const handleRevoke = () => {
    setApprovalState('revoked')
    setDispatchResult({
      status: 'revoked',
      message: isVi
        ? 'Đã thu hồi phiếu phê duyệt trước khi gửi ra bên ngoài.'
        : 'Approval token explicitly revoked before external dispatch.',
    })
  }

  const handleResetGate = () => {
    setBoundDigest('')
    setApprovalState('idle')
    setDispatchResult({ status: 'idle', message: '' })
  }

  const handleSimulateTamper = async () => {
    const referenceDigest = boundDigest || actionDigest
    if (!boundDigest) {
      setBoundDigest(referenceDigest)
      setApprovalState('approved')
    }
    const delta = intake.currency === 'VND' ? 9990000 : 9999
    const mutatedPayload: OpcActionPayload = {
      ...actionPayload,
      parameters: {
        ...actionPayload.parameters,
        amount: formatActionAmountString(financials.grandTotal + delta, intake.currency),
      },
    }
    const tamperedDigest = await computeSha256Hex(canonicalizePayload(mutatedPayload))
    setDispatchResult({
      status: 'tamper_detected',
      message: isVi
        ? `Chặn đứng giả mạo TOCTOU! Phiếu duyệt khóa vào mã ${referenceDigest.slice(
            0,
            16
          )}…, nhưng số tiền bị sửa trộm tạo ra mã ${tamperedDigest.slice(
            0,
            16
          )}…. Hệ thống hủy gửi ngay lập tức!`
        : `TOCTOU tamper blocked! Token bound to ${referenceDigest.slice(
            0,
            16
          )}…, but mutated amount produced ${tamperedDigest.slice(
            0,
            16
          )}…. Execution aborted!`,
    })
  }

  const handleSimulateReplay = () => {
    setDispatchResult({
      status: 'consumed',
      message: isVi
        ? 'ApprovalSecurityError: Phiếu duyệt chỉ có hiệu lực 1 lần duy nhất (consumed=true). Mọi lệnh phát lại đều bị từ chối.'
        : 'ApprovalSecurityError: Token already consumed (single-use replay guard).',
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-mono text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
            {isVi
              ? 'BUỒNG LÁI PILOT A · ZALO OA → BÁO GIÁ & VIETQR 1 CHẠM'
              : 'PILOT A COCKPIT · ZALO OA LEAD-TO-QUOTE & 1-TAP VIETQR'}
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {isVi
              ? 'Trợ Lý Báo Giá Zalo OA, VietQR Napas 247 & Nháp Hóa Đơn MISA/Sapo'
              : 'Zalo OA Lead-to-Quote, VietQR Napas 247 & MISA/Sapo Draft Cockpit'}
          </h2>
          <p className="text-xs text-neutral-400 max-w-3xl">
            {isVi
              ? 'Quy trình 4 bước an toàn cho Chủ doanh nghiệp SME: Bóc tách tin nhắn Zalo có trích dẫn câu gốc → Tính tiền + VAT + mã VietQR → Duyệt 1 chạm chống sửa giá → Sổ cái chi phí minh bạch.'
              : '4-Step Verified SME Loop: Zalo OA Intake with source_span citations → Decimal Quote + VAT + VietQR → Payload-Bound SHA-256 1-Tap Approval → Honest Usage Ledger.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* 1-Click Bilingual Toggle: Tiếng Việt | English */}
          <div
            role="group"
            aria-label="Language switcher"
            className="inline-flex items-center rounded-xl border border-emerald-500/30 bg-[#0b0f17] p-1"
          >
            <Languages className="w-3.5 h-3.5 text-emerald-400 ml-2 mr-1.5 shrink-0" />
            <button
              type="button"
              aria-pressed={isVi}
              onClick={() => setLanguage('vi')}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                isVi
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-neutral-300 hover:text-white'
              }`}
            >
              Tiếng Việt
            </button>
            <span className="text-neutral-600 px-0.5 select-none">|</span>
            <button
              type="button"
              aria-pressed={!isVi}
              onClick={() => setLanguage('en')}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                !isVi
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-neutral-300 hover:text-white'
              }`}
            >
              English
            </button>
          </div>

          {/* Optional Live FastAPI Gateway Sync Button */}
          <button
            type="button"
            onClick={() => void handleGatewayWebhookSync()}
            disabled={isSyncing}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-[#0b0f17] px-3.5 py-2 text-xs font-medium text-neutral-200 hover:border-emerald-500/40 hover:text-white disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${isSyncing ? 'animate-spin' : ''}`} />
            {isVi ? 'Đồng bộ Gateway' : 'Sync Gateway'}
          </button>

          <div className="hidden sm:flex rounded-xl border border-white/10 bg-[#0b0f17] px-3.5 py-2 font-mono text-xs items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <code className="text-emerald-300">mekong run --pack {packId}</code>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ClientIntakeCard
          value={intake}
          citations={citations}
          onChange={(next) => {
            setIntake(next)
          }}
        />
        <ProposalDraftPreview
          runId={runId}
          packId={packId}
          clientName={intake.clientName}
          clientContact={intake.clientContact}
          projectTitle={intake.projectTitle}
          principal={intake.principal}
          currency={intake.currency}
          language={intake.language}
          lineItems={lineItems}
          financials={financials}
          extractionConfidence={intake.extractionConfidence}
          citationCount={citations.length}
          missingFields={missingFields}
        />
        <CryptographicApprovalCard
          runId={runId}
          language={intake.language}
          timezone={intake.timezone}
          extractionConfidence={intake.extractionConfidence}
          isZaloWindowValid={isZaloWindowValid}
          actionDigest={actionDigest}
          boundDigest={boundDigest}
          payload={actionPayload}
          approvalState={approvalState}
          gatewaySync={gatewaySync}
          isSyncing={isSyncing}
          onApproveAndSend={handleApproveAndSend}
          onHandoffZalo={handleHandoffZalo}
          onRevoke={handleRevoke}
          onResetGate={handleResetGate}
          onSimulateTamper={handleSimulateTamper}
          onSimulateReplay={handleSimulateReplay}
          dispatchResult={dispatchResult}
        />
        <HonestUsageLedger
          runId={runId}
          language={intake.language}
          currency={intake.currency}
          selectedTier={selectedTier}
          onSelectTier={setSelectedTier}
          events={usageEvents}
          hasUnknownCosts={hasUnknownCosts}
          knownTotal={0}
        />
      </div>
    </div>
  )
}
