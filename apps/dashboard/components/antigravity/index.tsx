'use client'

import React from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { Cpu } from 'lucide-react'

export function UnifiedBridgeWidget() {
  return (
    <AgencyCard variant="glass" className="p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
          <Cpu className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">OPC Runtime Bridge</h3>
          <p className="text-[10px] font-mono text-emerald-400">mekong-runtime &gt;= 6.0</p>
        </div>
      </div>
      <p className="text-xs text-neutral-400 leading-relaxed">
        Connected to local SQLite WAL state &amp; Dual-Rail RaaS entitlement engine.
      </p>
    </AgencyCard>
  )
}
