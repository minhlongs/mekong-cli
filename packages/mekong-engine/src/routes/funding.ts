import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { createError, handleAsync, handleDb } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { validateTenantExists } from '../lib/route-utils'
import { logger } from '../lib/monitoring'
import {
  type CreateRoundInput,
  type CreateProjectInput,
  type ContributeInput,
  type FundingRound,
  type FundingProject,
  createRoundSchema,
  createProjectSchema,
  contributeSchema,
  ensureFundingTables,
  calculateQuadraticFunding,
} from './funding-schemas'

type Variables = { tenant: Tenant }
const fundingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
fundingRoutes.use('*', authMiddleware)

// Create funding round
fundingRoutes.post('/rounds', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  await validateTenantExists(c.env.DB!, tenant.id)
  await handleDb(() => ensureFundingTables(c.env.DB), 'DATABASE_ERROR', 'Failed to ensure funding tables exist')

  let body: CreateRoundInput
  try {
    body = createRoundSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const durationDays = body.duration_days || 14
  if (durationDays <= 0 || durationDays > 365) {
    return c.json(createError('VALIDATION_ERROR', 'duration_days must be between 1 and 365'), 400)
  }

  const now = new Date()
  const end = new Date(now.getTime() + durationDays * 24 * 60 * 60 * 1000)
  const id = crypto.randomUUID()

  await handleDb(
    () => c.env.DB!.prepare(
      'INSERT INTO funding_rounds (id, tenant_id, title, matching_pool, starts_at, ends_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, tenant.id, body.title, body.matching_pool, now.toISOString(), end.toISOString()).run(),
    'DATABASE_ERROR',
    'Failed to create funding round'
  )

  return c.json({ id, matching_pool: body.matching_pool, ends_at: end.toISOString(), status: 'active' }, 201)
}))

// Add project to round
fundingRoutes.post('/projects', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  let body: CreateProjectInput
  try {
    body = createProjectSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const round = await handleDb(
    () => c.env.DB!.prepare('SELECT id, status FROM funding_rounds WHERE id = ? AND tenant_id = ?').bind(body.round_id, tenant.id).first(),
    'DATABASE_ERROR',
    'Failed to validate funding round'
  )

  if (!round) return c.json(createError('NOT_FOUND', 'Funding round not found'), 404)
  if ((round as { status: string }).status !== 'active') return c.json(createError('CONFLICT', 'Funding round is not active'), 409)

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB!.prepare(
      'INSERT INTO funding_projects (id, round_id, tenant_id, name, description, author_id) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, body.round_id, tenant.id, body.name, body.description || '', body.author_id || null).run(),
    'DATABASE_ERROR',
    'Failed to add project to funding round'
  )

  return c.json({ id, round_id: body.round_id }, 201)
}))

// Contribute to project
fundingRoutes.post('/contribute', payloadSizeLimit(), handleAsync(async (c) => {
  let body: ContributeInput
  try {
    body = contributeSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    throw error
  }

  const id = crypto.randomUUID()
  try {
    await handleDb(
      () => c.env.DB!.prepare(
        'INSERT INTO funding_contributions (id, project_id, stakeholder_id, amount) VALUES (?, ?, ?, ?)'
      ).bind(id, body.project_id, body.stakeholder_id, body.amount).run(),
      'DATABASE_ERROR',
      'Failed to record contribution'
    )
  } catch (error) {
    if (error instanceof Error && error.message.includes('UNIQUE')) {
      return c.json(createError('CONFLICT', 'Already contributed to this project'), 409)
    }
    logger.error('Failed to record funding contribution', { error: error instanceof Error ? error.message : String(error), projectId: body.project_id })
    throw error
  }

  await handleDb(
    () => c.env.DB!.prepare(
      'UPDATE funding_projects SET total_contributions = total_contributions + ?, contributor_count = contributor_count + 1 WHERE id = ?'
    ).bind(body.amount, body.project_id).run(),
    'DATABASE_ERROR',
    'Failed to update project contribution totals'
  )

  return c.json({ id, amount: body.amount }, 201)
}))

// Calculate QF matching: matched = (Σ√ci)² - Σci
fundingRoutes.post('/rounds/:id/calculate', payloadSizeLimit(), handleAsync(async (c) => {
  const roundId = c.req.param('id')
  const db = c.env.DB!
  if (!db) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const round = await handleDb(
    () => db.prepare('SELECT * FROM funding_rounds WHERE id = ?').bind(roundId).first(),
    'DATABASE_ERROR',
    'Failed to fetch funding round'
  )
  if (!round) return c.json(createError('NOT_FOUND', 'Round not found'), 404)

  const projectsResult = await handleDb(
    async () => (await db.prepare('SELECT * FROM funding_projects WHERE round_id = ?').bind(roundId).all()) as unknown as { results?: FundingProject[] },
    'DATABASE_ERROR',
    'Failed to fetch projects for round'
  )

  const matchingPool = (round as FundingRound).matching_pool
  const results = await calculateQuadraticFunding(db, projectsResult.results || [], matchingPool)

  await handleDb(
    () => db.prepare("UPDATE funding_rounds SET status = 'completed' WHERE id = ?").bind(roundId).run(),
    'DATABASE_ERROR',
    'Failed to update round status to completed'
  )

  return c.json({
    round_id: roundId,
    matching_pool: matchingPool,
    results,
    note: 'QF: 10 people × $1 beats 1 person × $10 — democratic funding',
  })
}))

// List rounds
fundingRoutes.get('/rounds', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)
  await handleDb(() => ensureFundingTables(c.env.DB), 'DATABASE_ERROR', 'Failed to ensure funding tables exist')
  const rowsResult = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM funding_rounds WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?').bind(tenant.id, limit).all()) as unknown as { results?: FundingRound[] },
    'DATABASE_ERROR',
    'Failed to fetch funding rounds'
  )
  return c.json({ rounds: rowsResult.results, count: rowsResult.results?.length || 0 })
}))

export { fundingRoutes, createRoundSchema, createProjectSchema, contributeSchema, ensureFundingTables }
