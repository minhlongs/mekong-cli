import { NextResponse } from 'next/server'
import {
  guardDashboardApiRoute,
  isDashboardDemoMode,
  resolveEngineApiUrl,
} from '@/lib/demo-guard'

export const dynamic = 'force-dynamic'

export interface PilotKpiResponse {
  synthetic: boolean
  targets: {
    max_partners: number
    missions_per_partner_per_week: number
    feedback_sla_hours: number
  }
  totals: {
    redeemed_partners: number
    missions_submitted: number
    missions_completed: number
    missions_failed: number
    feedback_count: number
    feedback_within_48h_count: number
    feedback_within_48h_rate: number
    average_rating: number | null
  }
  partners: Array<{
    tenant_id: string
    missions_total: number
    missions_completed: number
    missions_failed: number
    feedback_submitted: number
    meets_weekly_target: boolean
  }>
}

const SYNTHETIC_PILOT_KPIS: PilotKpiResponse = {
  synthetic: true,
  targets: {
    max_partners: 5,
    missions_per_partner_per_week: 5,
    feedback_sla_hours: 48,
  },
  totals: {
    redeemed_partners: 5,
    missions_submitted: 27,
    missions_completed: 26,
    missions_failed: 1,
    feedback_count: 24,
    feedback_within_48h_count: 24,
    feedback_within_48h_rate: 1.0,
    average_rating: 4.8,
  },
  partners: [
    {
      tenant_id: 'pilot-partner-01 (Synthetic)',
      missions_total: 6,
      missions_completed: 6,
      missions_failed: 0,
      feedback_submitted: 6,
      meets_weekly_target: true,
    },
    {
      tenant_id: 'pilot-partner-02 (Synthetic)',
      missions_total: 5,
      missions_completed: 5,
      missions_failed: 0,
      feedback_submitted: 5,
      meets_weekly_target: true,
    },
    {
      tenant_id: 'pilot-partner-03 (Synthetic)',
      missions_total: 5,
      missions_completed: 5,
      missions_failed: 0,
      feedback_submitted: 4,
      meets_weekly_target: true,
    },
    {
      tenant_id: 'pilot-partner-04 (Synthetic)',
      missions_total: 6,
      missions_completed: 5,
      missions_failed: 1,
      feedback_submitted: 5,
      meets_weekly_target: true,
    },
    {
      tenant_id: 'pilot-partner-05 (Synthetic)',
      missions_total: 5,
      missions_completed: 5,
      missions_failed: 0,
      feedback_submitted: 4,
      meets_weekly_target: true,
    },
  ],
}

export async function GET(request: Request) {
  const blocked = guardDashboardApiRoute(request, { allowSyntheticGet: true })
  if (blocked) return blocked

  if (isDashboardDemoMode()) {
    return NextResponse.json(SYNTHETIC_PILOT_KPIS)
  }

  const serviceToken = process.env.SERVICE_TOKEN
  if (!serviceToken) {
    return NextResponse.json(SYNTHETIC_PILOT_KPIS)
  }

  try {
    const res = await fetch(`${resolveEngineApiUrl()}/billing/pilot-kpis`, {
      headers: { Authorization: `Bearer ${serviceToken}` },
    })
    if (!res.ok) {
      return NextResponse.json(SYNTHETIC_PILOT_KPIS)
    }
    const data = (await res.json()) as Omit<PilotKpiResponse, 'synthetic'>
    return NextResponse.json({ synthetic: false, ...data })
  } catch {
    return NextResponse.json(SYNTHETIC_PILOT_KPIS)
  }
}

export async function POST(request: Request) {
  const blocked = guardDashboardApiRoute(request)
  if (blocked) return blocked
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}
