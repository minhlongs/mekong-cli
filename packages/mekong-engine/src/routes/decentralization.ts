import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync, handleDb, createError } from '../types/error'
import {
  type CheckTransitionBody,
  PHASES,
  checkTransitionSchema,
  fetchTenantStakeholderMetrics,
} from './decentralization-helpers'

type Variables = { tenant: Tenant }

const decentralRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
decentralRoutes.use('*', authMiddleware)

// GET /status — current phase + power distribution + metrics + next phase requirements
decentralRoutes.get('/status', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant

  const { totalStakeholders, monthsActive, currentPhaseIndex } =
    await fetchTenantStakeholderMetrics(c.env.DB, tenant.id)

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

  const currentPhase = PHASES[currentPhaseIndex]!
  const nextPhase = PHASES[currentPhaseIndex + 1] ?? null

  const roleStatsResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        `SELECT role, COUNT(*) as count, SUM(reputation_score) as total_rep
     FROM stakeholders WHERE tenant_id = ? GROUP BY role`
      ).bind(tenant.id).all()
      return r as unknown as { results?: Array<{ role: string; count: number; total_rep: number }> }
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

  let _body: CheckTransitionBody
  try {
    _body = checkTransitionSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const { totalStakeholders, monthsActive, currentPhaseIndex } =
    await fetchTenantStakeholderMetrics(c.env.DB, tenant.id)

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

export { decentralRoutes, PHASES, checkTransitionSchema }
