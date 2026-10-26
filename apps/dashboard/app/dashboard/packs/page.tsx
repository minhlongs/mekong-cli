'use client'

import React from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { PackageCheck, ShieldAlert, Cpu, ArrowUpRight, CheckCircle2, Lock } from 'lucide-react'
import Link from 'next/link'

interface BusinessPackSummary {
  pack_id: string
  version: string
  schema_version: string
  license: string
  description: string
  capabilities: string[]
  approval_required: boolean
  cost_policy: string
  runtime: string
  jurisdiction: string
}

const REGISTERED_PACKS: BusinessPackSummary[] = [
  {
    pack_id: 'client-proposal-followup',
    version: '1.0.0',
    schema_version: 'opc-pack/v1',
    license: 'MIT',
    description: 'Autonomous Client Intake → Proposal Draft → Cryptographic Approval → Follow-up loop.',
    capabilities: ['proposal.generate_draft', 'followup.create_draft'],
    approval_required: true,
    cost_policy: 'honest_ledger (preserve unknown)',
    runtime: 'mekong-runtime>=6.0 (100% Offline)',
    jurisdiction: 'global (Multi-Currency & IANA)',
  },
  {
    pack_id: 'tax-tt78-compliance-vn',
    version: '1.2.0',
    schema_version: 'opc-pack/v1',
    license: 'MIT',
    description: 'Vietnam Circular TT78 electronic invoice audit, TNCN/TNDN calculations & tax declaration check.',
    capabilities: ['tax.audit_invoice', 'tax.calculate_tncn', 'tax.export_xml'],
    approval_required: true,
    cost_policy: 'honest_ledger (free offline core)',
    runtime: 'mekong-runtime>=6.0',
    jurisdiction: 'vn (VND currency)',
  },
  {
    pack_id: 'cross-border-retainer-ops',
    version: '0.9.5',
    schema_version: 'opc-pack/v1',
    license: 'MIT',
    description: 'International client retainer invoicing, Dual-Rail payment sync & automated SLA tracking.',
    capabilities: ['retainer.meter_hours', 'invoice.dispatch_dual_rail'],
    approval_required: true,
    cost_policy: 'honest_ledger',
    runtime: 'mekong-runtime>=6.0',
    jurisdiction: 'global (USD / EUR)',
  },
  {
    pack_id: 'creator-media-syndication',
    version: '1.1.0',
    schema_version: 'opc-pack/v1',
    license: 'MIT',
    description: 'Multi-platform media packaging, watermarking, and publish dispatch with human approval gate.',
    capabilities: ['media.transcode', 'publish.stage_release'],
    approval_required: true,
    cost_policy: 'honest_ledger',
    runtime: 'mekong-runtime>=6.0',
    jurisdiction: 'global',
  },
]

export default function BusinessPacksPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-mono text-emerald-400 mb-2">
            <PackageCheck className="w-3.5 h-3.5" />
            DECLARATIVE BUSINESS PACKS REGISTRY
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Registered OPC Packs (<code className="text-emerald-400">opc-pack/v1</code>)
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Static JSON manifests without dynamic code execution. Pure data schema, required capabilities & approval boundaries.
          </p>
        </div>

        <Link
          href="/dashboard/opc"
          className="rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 flex items-center gap-2 transition-colors"
        >
          <span>Open Interactive Cockpit</span>
          <ArrowUpRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {REGISTERED_PACKS.map((pack) => (
          <AgencyCard key={pack.pack_id} variant="glass" className="p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="text-base font-bold text-white font-mono">{pack.pack_id}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      v{pack.version}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-neutral-400 border border-white/10">
                      {pack.schema_version}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-neutral-400">
                      {pack.license}
                    </span>
                  </div>
                </div>
                <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
                  <Cpu className="w-4 h-4 text-emerald-400" />
                </div>
              </div>

              <p className="text-xs text-neutral-300 leading-relaxed mb-4">{pack.description}</p>

              <div className="space-y-2 text-xs font-mono">
                <div className="rounded-lg bg-[#06080d] p-3 border border-white/5 space-y-1.5">
                  <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Required Capabilities:</div>
                  <div className="flex flex-wrap gap-1">
                    {pack.capabilities.map((cap) => (
                      <span
                        key={cap}
                        className="rounded bg-white/5 border border-white/10 px-2 py-0.5 text-[11px] text-emerald-300"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                  <div className="rounded-lg bg-[#06080d] p-2.5 border border-white/5">
                    <div className="text-[10px] text-neutral-500">APPROVAL GATE</div>
                    <div className="flex items-center gap-1 text-emerald-400 font-bold mt-0.5">
                      <Lock className="w-3 h-3" />
                      MANDATORY SHA-256
                    </div>
                  </div>
                  <div className="rounded-lg bg-[#06080d] p-2.5 border border-white/5">
                    <div className="text-[10px] text-neutral-500">COST POLICY</div>
                    <div className="text-white font-medium truncate mt-0.5">{pack.cost_policy}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Manifest Validated
              </div>
              <Link
                href="/dashboard/opc"
                className="text-xs font-bold text-neutral-300 hover:text-emerald-400 flex items-center gap-1 transition-colors"
              >
                Run Pack in Cockpit
                <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </AgencyCard>
        ))}
      </div>
    </div>
  )
}
