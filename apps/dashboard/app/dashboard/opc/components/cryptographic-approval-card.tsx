'use client'

import React, { useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { ShieldCheck, ShieldAlert, KeyRound, Check, X, RefreshCcw, Bug } from 'lucide-react'
import type { OpcActionPayload } from '@/lib/opc-cockpit-data'

export type ApprovalState = 'idle' | 'approved' | 'rejected' | 'revoked' | 'consumed'

interface CryptographicApprovalCardProps {
  runId: string
  actionDigest: string
  payload: OpcActionPayload
  approvalState: ApprovalState
  onApprove: (revisionNotes: string) => void
  onReject: () => void
  onRevoke: () => void
  onSimulateDispatch: (tampered: boolean) => void
  dispatchResult: {
    status: 'idle' | 'success' | 'tamper_detected' | 'consumed' | 'revoked'
    message: string
  }
}

export default function CryptographicApprovalCard({
  runId,
  actionDigest,
  payload,
  approvalState,
  onApprove,
  onReject,
  onRevoke,
  onSimulateDispatch,
  dispatchResult,
}: CryptographicApprovalCardProps) {
  const [revisionNotes, setRevisionNotes] = useState('Reviewed scope & deliverables. Approved for draft creation.')
  const [simulateTamper, setSimulateTamper] = useState(false)

  const isApproved = approvalState === 'approved'
  const isConsumed = approvalState === 'consumed'
  const isRevoked = approvalState === 'revoked'
  const isRejected = approvalState === 'rejected'

  return (
    <AgencyCard variant="glass" className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <KeyRound className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">03 · Cryptographic Approval Gate</h3>
            <p className="text-[11px] text-neutral-500">
              Payload-bound SHA-256 action digest computed live. Single-use, non-repudiable.
            </p>
          </div>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase ${
            isApproved
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : isConsumed
              ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
              : isRevoked || isRejected
              ? 'bg-red-500/15 text-red-400 border border-red-500/30'
              : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
          }`}
        >
          {approvalState}
        </span>
      </div>

      <div className="rounded-xl border border-white/10 bg-[#06080d] p-4 space-y-3 font-mono">
        <div className="flex items-center justify-between text-[10px] text-neutral-500">
          <span className="flex items-center gap-1.5 text-neutral-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            CANONICAL ACTION DIGEST (SHA-256)
          </span>
          <span>RUN: {runId}</span>
        </div>
        <div className="rounded-lg bg-black/60 p-2.5 border border-white/5 text-[11px] text-emerald-300 break-all select-all font-mono">
          {actionDigest || 'Computing hash...'}
        </div>
        <div className="grid grid-cols-2 gap-2 text-[10px] text-neutral-400 pt-1 border-t border-white/5">
          <div>
            <span className="text-neutral-600 block">CAPABILITY:</span>
            <span className="text-white">{payload.capability}</span>
          </div>
          <div>
            <span className="text-neutral-600 block">CONNECTOR:</span>
            <span className="text-white">{payload.connector}</span>
          </div>
          <div>
            <span className="text-neutral-600 block">RECIPIENT:</span>
            <span className="text-white truncate block">{payload.recipient}</span>
          </div>
          <div>
            <span className="text-neutral-600 block">EXPIRES AT:</span>
            <span className="text-white">{new Date(payload.expires_at * 1000).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <label className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500 mb-1.5 block">
          Human Revision Notes (Audited)
        </label>
        <textarea
          rows={2}
          className="w-full rounded-xl border border-white/10 bg-[#06080d] px-3.5 py-2 text-xs text-white placeholder-neutral-600 focus:border-emerald-500/50 focus:outline-none"
          value={revisionNotes}
          onChange={(e) => setRevisionNotes(e.target.value)}
          disabled={isApproved || isConsumed}
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onApprove(revisionNotes)}
          disabled={isApproved || isConsumed}
          className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          <Check className="w-3.5 h-3.5" />
          Approve Token
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={isApproved || isConsumed || isRejected}
          className="flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs font-bold text-red-300 hover:bg-red-500/20 disabled:opacity-40 transition-all"
        >
          <X className="w-3.5 h-3.5" />
          Reject
        </button>
        <button
          type="button"
          onClick={onRevoke}
          disabled={!isApproved || isConsumed || isRevoked}
          className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-bold text-neutral-400 hover:text-white disabled:opacity-40 transition-all"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          Revoke
        </button>
      </div>

      <div className="mt-5 pt-4 border-t border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
            <Bug className="w-3.5 h-3.5 text-amber-400" />
            Adversarial Tamper Simulation
          </span>
          <label className="flex items-center gap-2 cursor-pointer text-xs text-neutral-300">
            <input
              type="checkbox"
              checked={simulateTamper}
              onChange={(e) => setSimulateTamper(e.target.checked)}
              className="accent-emerald-500 rounded"
            />
            <span className="text-[11px] font-mono text-amber-300">Mutate Payload Post-Approval</span>
          </label>
        </div>

        <button
          type="button"
          onClick={() => onSimulateDispatch(simulateTamper)}
          disabled={!isApproved}
          className="w-full rounded-lg border border-emerald-500/40 bg-emerald-500/10 py-2.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Dispatch to External Connector ({payload.connector})
        </button>

        {dispatchResult.status !== 'idle' && (
          <div
            className={`mt-3 rounded-lg border p-3 flex items-start gap-2.5 text-xs font-mono ${
              dispatchResult.status === 'success'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                : dispatchResult.status === 'tamper_detected'
                ? 'border-red-500/50 bg-red-500/10 text-red-200'
                : 'border-white/10 bg-white/5 text-neutral-300'
            }`}
          >
            {dispatchResult.status === 'success' ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-bold uppercase tracking-wider">
                {dispatchResult.status === 'tamper_detected'
                  ? 'CRITICAL · ApprovalSecurityError (Digest Mismatch)'
                  : dispatchResult.status.toUpperCase()}
              </div>
              <div className="text-[11px] mt-0.5 text-neutral-300">{dispatchResult.message}</div>
            </div>
          </div>
        )}
      </div>
    </AgencyCard>
  )
}
