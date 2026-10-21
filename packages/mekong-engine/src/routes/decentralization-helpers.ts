import { z } from 'zod'
import type { Bindings } from '../index'
import { handleDb } from '../types/error'

export const checkTransitionSchema = z.object({
  dry_run: z.boolean().optional().default(false),
})

export type CheckTransitionBody = z.infer<typeof checkTransitionSchema>

export type DecentralPhase = {
  name: string
  power_distribution: { leadership: number; founders: number; community: number }
  min_stakeholders: number
  min_months: number
  description: string
}

// Progressive decentralization phases — power distribution percentages
// [owner/admin, founders/experts, community/customers]
export const PHASES: DecentralPhase[] = [
  {
    name: 'foundation',
    power_distribution: { leadership: 50, founders: 25, community: 25 },
    min_stakeholders: 0,
    min_months: 0,
    description: 'Company-controlled — establishing product-market fit',
  },
  {
    name: 'growth',
    power_distribution: { leadership: 33, founders: 34, community: 33 },
    min_stakeholders: 20,
    min_months: 12,
    description: 'Balanced triangle — proven PMF, scaling operations',
  },
  {
    name: 'maturity',
    power_distribution: { leadership: 25, founders: 40, community: 35 },
    min_stakeholders: 100,
    min_months: 18,
    description: 'Community gaining weight — ecosystem self-sustaining',
  },
  {
    name: 'full_inversion',
    power_distribution: { leadership: 20, founders: 45, community: 35 },
    min_stakeholders: 500,
    min_months: 24,
    description: 'Tam giác ngược complete — community at apex',
  },
]

export function resolveCurrentPhaseIndex(totalStakeholders: number, monthsActive: number): number {
  for (let i = PHASES.length - 1; i >= 0; i--) {
    const phase = PHASES[i]!
    if (totalStakeholders >= phase.min_stakeholders && monthsActive >= phase.min_months) {
      return i
    }
  }
  return 0
}

export async function fetchTenantStakeholderMetrics(
  db: NonNullable<Bindings['DB']>,
  tenantId: string
): Promise<{ totalStakeholders: number; monthsActive: number; currentPhaseIndex: number }> {
  const stakeholderCountResult = await handleDb(
    async () => {
      const r = await db.prepare(
        'SELECT COUNT(*) as count FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenantId).first()
      return r as { count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to count stakeholders'
  )
  const totalStakeholders = stakeholderCountResult?.count || 0

  const firstStakeholderResult = await handleDb(
    async () => {
      const r = await db.prepare(
        'SELECT MIN(created_at) as first FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenantId).first()
      return r as { first: string | null } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch first stakeholder'
  )

  let monthsActive = 0
  if (firstStakeholderResult?.first) {
    const diffMs = Date.now() - new Date(firstStakeholderResult.first).getTime()
    monthsActive = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 30))
  }

  const currentPhaseIndex = resolveCurrentPhaseIndex(totalStakeholders, monthsActive)
  return { totalStakeholders, monthsActive, currentPhaseIndex }
}
