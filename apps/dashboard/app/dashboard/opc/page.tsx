'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { ShieldCheck, Terminal } from 'lucide-react'
import ClientIntakeCard, { type ClientIntake } from './components/client-intake-card'
import ProposalDraftPreview from './components/proposal-draft-preview'
import CryptographicApprovalCard, { type ApprovalState } from './components/cryptographic-approval-card'
import HonestUsageLedger from './components/honest-usage-ledger'
import {
  SERVICE_CATALOG,
  canonicalizePayload,
  computeSha256Hex,
  type OpcActionPayload,
  type OpcLineItem,
  type OpcUsageEvent,
} from '@/lib/opc-cockpit-data'

const FIXED_EXPIRES_AT = 1800000000

const INITIAL_INTAKE: ClientIntake = {
  requestId: 'req_sample_2026_001',
  clientName: 'Horizon Fintech Group',
  clientContact: 'procurement@horizon-example.invalid',
  projectTitle: 'Zero-Downtime Multi-Region API Gateway Upgrade',
  estimatedHours: 20,
  currency: 'USD',
  timezone: 'UTC',
  language: 'en',
  services: ['architecture_review', 'security_audit'],
  attachments: ['rfp_architecture_v1.pdf'],
  principal: 'Alex Nguyen',
}

export default function OpcCockpitPage() {
  const [intake, setIntake] = useState<ClientIntake>(INITIAL_INTAKE)
  const [actionDigest, setActionDigest] = useState<string>('')
  const [boundDigest, setBoundDigest] = useState<string>('')
  const [approvalState, setApprovalState] = useState<ApprovalState>('idle')
  const [dispatchResult, setDispatchResult] = useState<{
    status: 'idle' | 'success' | 'tamper_detected' | 'consumed' | 'revoked'
    message: string
  }>({ status: 'idle', message: '' })

  const runId = 'run_opc2027_8f3a91c2b4e0'
  const packId = 'client-proposal-followup'

  const { lineItems, totalAmount, missingFields } = useMemo(() => {
    const items: OpcLineItem[] = []
    let total = 0
    const missing: string[] = []
    const svcCount = Math.max(1, intake.services.length)
    const hoursPerSvc = Math.max(1, Math.floor(intake.estimatedHours / svcCount))

    for (const svcKey of intake.services) {
      const def = SERVICE_CATALOG[svcKey]
      const rate = def ? def.rates[intake.currency] : null
      if (rate === null || rate === undefined) {
        missing.push(`Unpriced service: '${svcKey}'`)
        items.push({
          service: svcKey,
          hours: hoursPerSvc,
          rate: 0,
          subtotal: 0,
          isUnpriced: true,
        })
      } else {
        const sub = rate * hoursPerSvc
        total += sub
        items.push({
          service: svcKey,
          hours: hoursPerSvc,
          rate,
          subtotal: sub,
          isUnpriced: false,
        })
      }
    }
    return { lineItems: items, totalAmount: total, missingFields: missing }
  }, [intake.services, intake.estimatedHours, intake.currency])

  const actionPayload: OpcActionPayload = useMemo(
    () => ({
      attachments: intake.attachments,
      budget_amount: '0.00',
      budget_currency: intake.currency,
      capability: 'followup.create_draft',
      connector: 'mock_followup_draft',
      content: `Draft proposal for ${intake.projectTitle} is ready for review.`,
      expires_at: FIXED_EXPIRES_AT,
      parameters: {
        amount: totalAmount.toFixed(2),
        project_title: intake.projectTitle,
      },
      principal: intake.principal,
      recipient: intake.clientContact,
    }),
    [intake, totalAmount]
  )

  useEffect(() => {
    const canonical = canonicalizePayload(actionPayload)
    computeSha256Hex(canonical).then((hex) => {
      setActionDigest(hex)
    })
  }, [actionPayload])

  const hasUnknownCosts = missingFields.length > 0

  const usageEvents: OpcUsageEvent[] = useMemo(() => {
    const base: OpcUsageEvent[] = [
      {
        event_id: 'use_est_001',
        run_id: runId,
        stage: 'estimated',
        provider: 'opc_pack_planner',
        model: 'opc-pack/v1',
        tokens: 148,
        amount: '0.00',
        currency: intake.currency,
        pricing_source: 'manifest_policy',
      },
      {
        event_id: 'use_res_002',
        run_id: runId,
        stage: 'reserved',
        provider: 'mcu_credit_store',
        model: 'sqlite_wal_guard',
        tokens: 0,
        amount: '0.00',
        currency: intake.currency,
        pricing_source: 'local_offline',
      },
      {
        event_id: 'use_act_003',
        run_id: runId,
        stage: 'actual',
        provider: 'deterministic_engine',
        model: 'offline_rules',
        tokens: 84,
        amount: '0.00',
        currency: intake.currency,
        pricing_source: 'local_offline',
      },
    ]

    if (hasUnknownCosts) {
      base.push({
        event_id: 'use_unk_004',
        run_id: runId,
        stage: 'unknown',
        provider: 'custom_connector_bespoke',
        model: 'external_unpriced_api',
        tokens: 312,
        amount: null,
        currency: intake.currency,
        pricing_source: 'unpriced_external',
      })
    }
    return base
  }, [intake.currency, hasUnknownCosts])

  const handleApprove = () => {
    setBoundDigest(actionDigest)
    setApprovalState('approved')
    setDispatchResult({
      status: 'idle',
      message: '',
    })
  }

  const handleReject = () => {
    setApprovalState('rejected')
    setDispatchResult({
      status: 'revoked',
      message: 'Token decision set to REJECT. Connector execution blocked.',
    })
  }

  const handleRevoke = () => {
    setApprovalState('revoked')
    setDispatchResult({
      status: 'revoked',
      message: 'Approval token explicitly revoked before consumption.',
    })
  }

  const handleSimulateDispatch = async (tampered: boolean) => {
    if (approvalState === 'consumed') {
      setDispatchResult({
        status: 'consumed',
        message: 'ApprovalSecurityError: Token already consumed (single-use replay guard).',
      })
      return
    }
    if (tampered) {
      const mutated: OpcActionPayload = {
        ...actionPayload,
        parameters: {
          ...actionPayload.parameters,
          amount: `${(totalAmount + 9999).toFixed(2)}`,
        },
      }
      const tamperedDigest = await computeSha256Hex(canonicalizePayload(mutated))
      setDispatchResult({
        status: 'tamper_detected',
        message: `Token bound to ${boundDigest.slice(0, 16)}…, but mutated payload produced ${tamperedDigest.slice(0, 16)}… Execution aborted!`,
      })
      return
    }
    if (boundDigest !== actionDigest) {
      setDispatchResult({
        status: 'tamper_detected',
        message: `Intake modified after approval! Bound ${boundDigest.slice(0, 16)}… != current ${actionDigest.slice(0, 16)}…`,
      })
      return
    }
    setApprovalState('consumed')
    setDispatchResult({
      status: 'success',
      message: `Dispatched idempotently via ${actionPayload.connector} (key: idem_${actionDigest.slice(0, 12)}). Token marked consumed=true.`,
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-mono text-emerald-400 mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            OPC 2027 AGENTIC COCKPIT · CRYPTOGRAPHIC GLASS
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            One-Person Company Autonomous Workflow Cockpit
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            4-Step Verified Loop: Client Intake → Proposal Draft → Payload-Bound SHA-256 Approval Gate → Honest Usage Ledger.
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-[#0b0f17] px-4 py-2.5 font-mono text-xs flex items-center gap-2.5">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="text-neutral-400">CLI:</span>
          <code className="text-emerald-300">mekong run --pack {packId}</code>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ClientIntakeCard value={intake} onChange={setIntake} />
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
          totalAmount={totalAmount}
          missingFields={missingFields}
        />
        <CryptographicApprovalCard
          runId={runId}
          actionDigest={actionDigest}
          payload={actionPayload}
          approvalState={approvalState}
          onApprove={handleApprove}
          onReject={handleReject}
          onRevoke={handleRevoke}
          onSimulateDispatch={handleSimulateDispatch}
          dispatchResult={dispatchResult}
        />
        <HonestUsageLedger
          runId={runId}
          currency={intake.currency}
          events={usageEvents}
          hasUnknownCosts={hasUnknownCosts}
          knownTotal={0}
        />
      </div>
    </div>
  )
}
