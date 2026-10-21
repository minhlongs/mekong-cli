'use client'

import React from 'react'
import { SyntheticMetricBadge } from '@/components/ui/synthetic-data-banner'

export function UnifiedBridgeWidget() {
  return (
    <div className="p-5 rounded-xl bg-white/[0.02] border border-white/10">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-white">
          Pilot Mission Bridge Overview (Synthetic Demo)
        </h3>
        <SyntheticMetricBadge />
      </div>
      <p className="text-xs text-neutral-400">
        Displaying synthetic pilot telemetry only. Partner missions run in isolated Engine tenants at api.cashclaw.cc.
      </p>
    </div>
  )
}
