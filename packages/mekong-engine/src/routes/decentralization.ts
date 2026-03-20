import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync, handleDb, createError } from '../types/error'

type Variables = { tenant: Tenant }

// Zod schema for POST /check-transition body
// Endpoint accepts empty body or optional dry_run flag
const checkTransitionSchema = z.object({
  dry_run: z.boolean().optional().default(false),
})

type CheckTransitionBody = z.infer<typeof checkTransitionSchema>

const decentralRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
decentralRoutes.use('*', authMiddleware)

// Progressive decentralization phases — power distribution percentages
// [owner/admin, founders/experts, community/customers]
export const PHASES = [
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

// GET /status — current phase + power distribution + metrics + next phase requirements
decentralRoutes.get('/status', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant

  // Count stakeholders
  const stakeholderCountResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        'SELECT COUNT(*) as count FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenant.id).first()
      return r as { count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to count stakeholders'
  )
  const totalStakeholders = stakeholderCountResult?.count || 0

  // Calculate months since first stakeholder
  const firstStakeholderResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        'SELECT MIN(created_at) as first FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenant.id).first()
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

  // Count proposals passed (governance maturity signal)
  const passedProposalsResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        "SELECT COUNT(*) as count FROM proposals WHERE tenant_id = ? AND status = 'approved'"
      ).bind(tenant.id).first()
      return r as { count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to count proposals'
  )

  // Determine current phase
  let currentPhaseIndex = 0
  for (let i = PHASES.length - 1; i >= 0; i--) {
    const phase = PHASES[i]!
    if (totalStakeholders >= phase.min_stakeholders && monthsActive >= phase.min_months) {
      currentPhaseIndex = i
      break
    }
  }

  const currentPhase = PHASES[currentPhaseIndex]!
  const nextPhase = PHASES[currentPhaseIndex + 1] ?? null

  // Community vs leadership vote weight from recent proposals
  const roleStatsResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        `SELECT role, COUNT(*) as count, SUM(reputation_score) as total_rep
     FROM stakeholders WHERE tenant_id = ? GROUP BY role`
      ).bind(tenant.id).all()
      return r as { results?: { role: string; count: number; total_rep: number }[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch role stats'
  )

  const roleBreakdown: Record<string, { count: number; total_rep: number }> = {}
  for (const row of roleStatsResult.results || []) {
    roleBreakdown[row.role] = {
      count: row.count,
      total_rep: row.total_rep || 0,
    }
  }

  return c.json({
    current_phase: {
      index: currentPhaseIndex,
      name: currentPhase.name,
      description: currentPhase.description,
      power_distribution: currentPhase.power_distribution,
    },
    metrics: {
      total_stakeholders: totalStakeholders,
      months_active: monthsActive,
      proposals_passed: passedProposalsResult?.count || 0,
      role_breakdown: roleBreakdown,
    },
    next_phase: nextPhase
      ? {
          name: nextPhase.name,
          power_distribution: nextPhase.power_distribution,
          requirements: {
            min_stakeholders: nextPhase.min_stakeholders,
            min_months: nextPhase.min_months,
          },
          progress: {
            stakeholders: `${totalStakeholders}/${nextPhase.min_stakeholders}`,
            months: `${monthsActive}/${nextPhase.min_months}`,
          },
        }
      : null,
    all_phases: PHASES,
  })
}))

// POST /check-transition — evaluate eligibility for next phase
decentralRoutes.post('/check-transition', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant

  // Validate request body
  let body: CheckTransitionBody
  try {
    body = checkTransitionSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const stakeholderCountResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        'SELECT COUNT(*) as count FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenant.id).first()
      return r as { count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to count stakeholders'
  )
  const totalStakeholders = stakeholderCountResult?.count || 0

  const firstStakeholderResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        'SELECT MIN(created_at) as first FROM stakeholders WHERE tenant_id = ?'
      ).bind(tenant.id).first()
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

  // Find current phase
  let currentPhaseIndex = 0
  for (let i = PHASES.length - 1; i >= 0; i--) {
    const phase = PHASES[i]!
    if (totalStakeholders >= phase.min_stakeholders && monthsActive >= phase.min_months) {
      currentPhaseIndex = i
      break
    }
  }

  const currentPhaseName = PHASES[currentPhaseIndex]!.name
  const nextPhase = PHASES[currentPhaseIndex + 1]
  if (!nextPhase) {
    return c.json({
      eligible: false,
      message: 'Already at maximum decentralization phase (full_inversion)',
      current_phase: currentPhaseName,
    })
  }

  const stakeholdersMet = totalStakeholders >= nextPhase.min_stakeholders
  const monthsMet = monthsActive >= nextPhase.min_months
  const eligible = stakeholdersMet && monthsMet

  const gaps: string[] = []
  if (!stakeholdersMet) {
    gaps.push(`Need ${nextPhase.min_stakeholders - totalStakeholders} more stakeholders`)
  }
  if (!monthsMet) {
    gaps.push(`Need ${nextPhase.min_months - monthsActive} more months`)
  }

  return c.json({
    eligible,
    current_phase: currentPhaseName,
    target_phase: nextPhase.name,
    checks: {
      stakeholders: { required: nextPhase.min_stakeholders, actual: totalStakeholders, met: stakeholdersMet },
      months: { required: nextPhase.min_months, actual: monthsActive, met: monthsMet },
    },
    gaps,
    message: eligible
      ? `Ready to transition to ${nextPhase.name} phase`
      : `Not yet eligible: ${gaps.join('; ')}`,
  })
}))

export { decentralRoutes }
