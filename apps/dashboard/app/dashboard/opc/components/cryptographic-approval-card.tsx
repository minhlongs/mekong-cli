'use client'

import React, { useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import {
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  RefreshCcw,
  Wifi,
  WifiOff,
  RotateCcw,
} from 'lucide-react'
import {
  MIN_EXTRACTION_CONFIDENCE,
  formatDeterministicTimestamp,
  type GatewaySyncResult,
  type OpcActionPayload,
  type SupportedLanguage,
} from '@/lib/opc-cockpit-data'

export type ApprovalState = 'idle' | 'approved' | 'rejected' | 'revoked' | 'consumed'

export interface DispatchOutcome {
  status: 'idle' | 'success' | 'tamper_detected' | 'consumed' | 'revoked'
  message: string
}

interface CryptographicApprovalCardProps {
  runId: string
  language: SupportedLanguage
  timezone: string
  extractionConfidence: number
  isZaloWindowValid: boolean
  actionDigest: string
  boundDigest: string
  payload: OpcActionPayload
  approvalState: ApprovalState
  gatewaySync: GatewaySyncResult
  isSyncing: boolean
  onApproveAndSend: (revisionNotes: string) => Promise<void>
  onHandoffZalo: (revisionNotes: string) => Promise<void>
  onRevoke: () => void
  onResetGate: () => void
  onSimulateTamper: () => Promise<void>
  onSimulateReplay: () => void
  dispatchResult: DispatchOutcome
}

const STATE_LABELS_VI: Record<ApprovalState, string> = {
  idle: 'CHỜ DUYỆT 1 CHẠM',
  approved: 'ĐÃ KÝ DUYỆT',
  consumed: 'ĐÃ GỬI (KHÓA 1 LẦN)',
  revoked: 'ĐÃ THU HỒI / CHUYỂN CHAT TAY',
  rejected: 'ĐÃ TỪ CHỐI',
}

const STATE_LABELS_EN: Record<ApprovalState, string> = {
  idle: 'PENDING 1-TAP APPROVAL',
  approved: 'SIGNED & BOUND',
  consumed: 'DISPATCHED (SINGLE-USE)',
  revoked: 'REVOKED / LIVE HANDOFF',
  rejected: 'REJECTED',
}

export default function CryptographicApprovalCard({
  runId,
  language,
  timezone,
  extractionConfidence,
  isZaloWindowValid,
  actionDigest,
  boundDigest,
  payload,
  approvalState,
  gatewaySync,
  isSyncing,
  onApproveAndSend,
  onHandoffZalo,
  onRevoke,
  onResetGate,
  onSimulateTamper,
  onSimulateReplay,
  dispatchResult,
}: CryptographicApprovalCardProps) {
  const isVi = language === 'vi'
  const [revisionNotes, setRevisionNotes] = useState(
    'Đã kiểm tra số tiền báo giá, thuế GTGT & mã VietQR. Đồng ý gửi cho khách qua Zalo OA.'
  )

  const isConsumed = approvalState === 'consumed'
  const isRevoked = approvalState === 'revoked'
  const isRejected = approvalState === 'rejected'
  const isLowConfidence = extractionConfidence < MIN_EXTRACTION_CONFIDENCE
  const hasValidDigest = actionDigest.length === 64
  const canApproveAuto =
    !isConsumed && !isLowConfidence && isZaloWindowValid && !isSyncing && hasValidDigest

  const formattedExpiry = formatDeterministicTimestamp(payload.expires_at, timezone, language)

  return (
    <AgencyCard variant="glass" className="p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <KeyRound className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isVi
                ? '03 · Phê Duyệt 1 Chạm & Khóa Chống Sửa Đổi (SHA-256)'
                : '03 · Payload-Bound 1-Tap Approval & TOCTOU Guard'}
            </h3>
            <p className="text-[11px] text-neutral-400">
              {isVi
                ? 'Chữ ký số SHA-256 gắn chặt vào tổng tiền & người nhận. Sửa 1 ký tự sau khi ký sẽ tự động hủy gửi.'
                : 'Web Crypto SHA-256 digest binds exact quote amount & recipient. Single-use, non-repudiable.'}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-mono border ${
              gatewaySync.mode === 'live_gateway' && gatewaySync.synced
                ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300'
                : gatewaySync.mode === 'failed_closed'
                ? 'border-red-500/40 bg-red-500/15 text-red-300'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
            }`}
          >
            {gatewaySync.mode === 'live_gateway' && gatewaySync.synced ? (
              <Wifi className="w-3 h-3" />
            ) : (
              <WifiOff className="w-3 h-3" />
            )}
            {gatewaySync.mode === 'live_gateway' && gatewaySync.synced
              ? isVi
                ? 'BFF · FastAPI Đã Xác Thực'
                : 'BFF · Gateway Verified'
              : gatewaySync.mode === 'failed_closed'
              ? isVi
                ? 'BFF Khóa An Toàn (Fail-Closed)'
                : 'BFF Fail-Closed'
              : isVi
              ? 'Chưa Đồng Bộ BFF'
              : 'BFF Unsynced'}
          </span>

          <span
            className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase ${
              approvalState === 'approved'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : isConsumed
                ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                : isRevoked || isRejected
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'bg-neutral-500/15 text-neutral-300 border border-white/15'
            }`}
          >
            {isVi ? STATE_LABELS_VI[approvalState] : STATE_LABELS_EN[approvalState]}
          </span>
        </div>
      </div>

      {/* Cryptographic Digest Summary */}
      <div className="rounded-xl border border-white/10 bg-[#06080d] p-4 space-y-3 font-mono">
        <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-neutral-400">
          <span className="flex items-center gap-1.5 text-neutral-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            {isVi ? 'MÃ BĂM BÁO GIÁ (SHA-256 PAYLOAD DIGEST)' : 'CANONICAL ACTION DIGEST (SHA-256)'}
          </span>
          <span>RUN: {runId}</span>
        </div>

        <div className="rounded-lg bg-black/60 p-2.5 border border-white/5 text-[11px] text-emerald-300 break-all select-all font-mono">
          {actionDigest || (isVi ? 'Đang tính mã băm SHA-256...' : 'Computing SHA-256 hash...')}
        </div>

        {boundDigest && (
          <div className="text-[10px] text-neutral-400 flex flex-wrap items-center justify-between gap-1">
            <span>
              {isVi ? 'Mã đã khóa khi bấm duyệt:' : 'Signed Digest Bound:'}{' '}
              <code className="text-emerald-300">{boundDigest.slice(0, 20)}…</code>
            </span>
            <span
              className={
                boundDigest === actionDigest ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'
              }
            >
              {boundDigest === actionDigest
                ? isVi
                  ? 'KHỚP 100%'
                  : 'MATCH VERIFIED'
                : isVi
                ? 'LỆCH DỮ LIỆU SAU KÝ!'
                : 'DIGEST DRIFT DETECTED!'}
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-[10px] text-neutral-400 pt-2 border-t border-white/5">
          <div>
            <span className="text-neutral-500 block">
              {isVi ? 'KÊNH GỬI & HÀNH ĐỘNG:' : 'CONNECTOR & CAPABILITY:'}
            </span>
            <span className="text-white">
              {payload.connector} · {payload.capability}
            </span>
          </div>
          <div>
            <span className="text-neutral-500 block">
              {isVi ? 'NGƯỜI NHẬN TRÊN ZALO OA:' : 'ZALO OA RECIPIENT:'}
            </span>
            <span className="text-white truncate block">{payload.recipient}</span>
          </div>
          <div className="sm:col-span-2">
            <span className="text-neutral-500 block">
              {isVi
                ? 'HẠN HIỆU LỰC PHIẾU DUYỆT (TỰ HỦY SAU 24H):'
                : 'TOKEN EXPIRY TIMESTAMP (24H TTL):'}
            </span>
            <span className="text-emerald-300">
              {formattedExpiry} ({timezone})
            </span>
          </div>
        </div>
      </div>

      {/* Audited Owner Notes */}
      <div className="mt-4">
        <label
          htmlFor="opc-revision-notes"
          className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400 mb-1.5 block"
        >
          {isVi ? 'Ghi chú của chủ doanh nghiệp (Lưu nhật ký kiểm toán)' : 'Owner Approval Notes (Audited)'}
        </label>
        <textarea
          id="opc-revision-notes"
          rows={2}
          className="w-full rounded-xl border border-white/10 bg-[#06080d] px-3.5 py-2 text-xs text-white placeholder-neutral-600 focus:border-emerald-500/50 focus:outline-none"
          value={revisionNotes}
          onChange={(e) => setRevisionNotes(e.target.value)}
          disabled={isConsumed}
        />
      </div>

      {/* Guardrail Warning when <85% Confidence or >48h Zalo Window */}
      {(isLowConfidence || !isZaloWindowValid) && (
        <div className="mt-3 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3.5 py-2.5 text-[11px] text-amber-200">
          {isLowConfidence
            ? isVi
              ? 'Nút gửi tự động đang tạm khóa vì độ tin cậy dưới 85%. Vui lòng bấm "👤 Chuyển Chat Tay Zalo OA" hoặc kiểm tra lại nội dung bóc tách.'
              : '1-Tap auto-dispatch is locked because extraction confidence is below 85%. Use Zalo OA Live Handoff.'
            : isVi
            ? 'Đã quá khung 48h tương tác miễn phí của Zalo OA. Vui lòng chuyển nhân viên chăm sóc trực tiếp.'
            : 'Zalo OA 48h interaction window expired. Please hand off to a human operator.'}
        </div>
      )}

      {/* Primary Mobile-First 1-Tap Action Buttons */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <button
          type="button"
          onClick={() => void onApproveAndSend(revisionNotes)}
          disabled={!canApproveAuto}
          className="w-full min-h-[46px] flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs sm:text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/15"
        >
          {isVi
            ? '✅ Duyệt & Gửi Báo Giá + VietQR'
            : '✅ Approve & Send Quote + VietQR'}
        </button>

        <button
          type="button"
          onClick={() => void onHandoffZalo(revisionNotes)}
          disabled={isSyncing}
          className="w-full min-h-[46px] flex items-center justify-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/15 px-4 py-2.5 text-xs sm:text-sm font-bold text-amber-200 hover:bg-amber-500/25 disabled:opacity-40 transition-all"
        >
          {isVi
            ? '👤 Chuyển Chat Tay Zalo OA'
            : '👤 Handoff to Zalo OA Live Chat'}
        </button>
      </div>

      {/* Security Verification & TOCTOU Tamper Simulation */}
      <div className="mt-4 pt-4 border-t border-white/10 space-y-2.5">
        <button
          type="button"
          onClick={() => void onSimulateTamper()}
          className="w-full min-h-[42px] rounded-xl border border-red-500/35 bg-red-500/10 px-3.5 py-2.5 text-xs font-bold text-red-200 hover:bg-red-500/20 transition-all"
        >
          {isVi
            ? '🔄 Mô phỏng sửa đổi sau khi ký (Test chống giả mạo TOCTOU)'
            : '🔄 Simulate Post-Signing Mutation (Test TOCTOU Tamper Guard)'}
        </button>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onSimulateReplay}
            disabled={!isConsumed}
            className="flex-1 min-w-[140px] flex items-center justify-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-medium text-neutral-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCcw className="w-3 h-3" />
            {isVi ? 'Thử gửi trùng lần 2 (Test Replay)' : 'Test Duplicate Send (Replay)'}
          </button>

          <button
            type="button"
            onClick={onRevoke}
            disabled={isConsumed || isRevoked}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-medium text-neutral-300 hover:text-white disabled:opacity-40 transition-colors"
          >
            {isVi ? 'Thu hồi phiếu' : 'Revoke'}
          </button>

          <button
            type="button"
            onClick={onResetGate}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-medium text-neutral-300 hover:text-white transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            {isVi ? 'Đặt lại' : 'Reset'}
          </button>
        </div>

        {dispatchResult.status !== 'idle' && (
          <div
            role="status"
            aria-live="polite"
            className={`mt-2 rounded-xl border p-3.5 flex items-start gap-2.5 text-xs font-mono ${
              dispatchResult.status === 'success'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                : dispatchResult.status === 'tamper_detected'
                ? 'border-red-500/50 bg-red-500/10 text-red-200'
                : dispatchResult.status === 'consumed'
                ? 'border-blue-500/40 bg-blue-500/10 text-blue-200'
                : 'border-amber-500/40 bg-amber-500/10 text-amber-200'
            }`}
          >
            {dispatchResult.status === 'success' ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            )}
            <div className="min-w-0">
              <div className="font-bold uppercase tracking-wider">
                {dispatchResult.status === 'tamper_detected'
                  ? 'CRITICAL · ApprovalSecurityError (SHA-256 Digest Mismatch)'
                  : dispatchResult.status === 'consumed'
                  ? 'BLOCKED · ApprovalSecurityError (Single-Use Replay Guard)'
                  : dispatchResult.status.toUpperCase()}
              </div>
              <div className="text-[11px] mt-1 text-neutral-200 break-words">
                {dispatchResult.message}
              </div>
            </div>
          </div>
        )}
      </div>
    </AgencyCard>
  )
}
