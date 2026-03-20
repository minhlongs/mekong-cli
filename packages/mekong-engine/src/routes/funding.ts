import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { createError, handleAsync, handleDb, HttpError } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { validateTenantExists } from '../lib/route-utils'

type Variables = { tenant: Tenant }
const fundingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
fundingRoutes.use('*', authMiddleware)

// Zod schemas
const createRoundSchema = z.object({
  title: z.string().min(1, 'title is required').max(200, 'title must be ≤200 chars'),
  matching_pool: z.number().int().positive('matching_pool must be positive').max(10_000_000_000, 'matching_pool too large'),
  duration_days: z.number().int().positive('duration_days must be positive').max(365, 'duration_days must be ≤365').optional(),
})
type CreateRoundInput = z.infer<typeof createRoundSchema>

const createProjectSchema = z.object({
  round_id: z.string().uuid('round_id must be a valid UUID'),
  name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
  description: z.string().max(1000, 'description must be ≤1000 chars').optional(),
  author_id: z.string().uuid('author_id must be a valid UUID').optional(),
})
type CreateProjectInput = z.infer<typeof createProjectSchema>

const contributeSchema = z.object({
  project_id: z.string().uuid('project_id must be a valid UUID'),
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  amount: z.number().int().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
})
type ContributeInput = z.infer<typeof contributeSchema>

/**
 * Ensure funding tables exist - using safe batched statements instead of .exec()
 * This prevents SQL injection risks from raw SQL strings
 */
async function ensureFundingTables(db: Bindings['DB']) {
  if (!db) return

  // Check if tables exist first (avoid redundant creation attempts)
  const checkResult = await db
    .prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='funding_rounds'")
    .first()

  if (checkResult) return // Tables already exist

  // Create tables using batched statements (safer than .exec())
  const batch = [
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_rounds (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
        matching_pool INTEGER NOT NULL DEFAULT 0,
        status TEXT DEFAULT 'active' CHECK (status IN ('active','calculating','completed')),
        starts_at TEXT, ends_at TEXT, created_at TEXT DEFAULT (datetime('now'))
      )
    `),
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_projects (
        id TEXT PRIMARY KEY, round_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
        name TEXT NOT NULL, description TEXT, author_id TEXT,
        total_contributions INTEGER DEFAULT 0, contributor_count INTEGER DEFAULT 0,
        matched_amount INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
      )
    `),
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_contributions (
        id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stakeholder_id TEXT NOT NULL,
        amount INTEGER NOT NULL, created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(project_id, stakeholder_id)
      )
    `),
  ]

  await db.batch(batch)
}

// Create funding round
fundingRoutes.post('/rounds', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  // Validate tenant exists (defense in depth)
  await validateTenantExists(c.env.DB, tenant.id)

  await handleDb(
    () => ensureFundingTables(c.env.DB),
    'DATABASE_ERROR',
    'Failed to ensure funding tables exist'
  )

  let body: CreateRoundInput
  try {
    body = createRoundSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  // Edge case: Validate duration bounds
  const durationDays = body.duration_days || 14
  if (durationDays <= 0 || durationDays > 365) {
    return c.json(createError('VALIDATION_ERROR', 'duration_days must be between 1 and 365'), 400)
  }

  const now = new Date()
  const end = new Date(now.getTime() + durationDays * 24 * 60 * 60 * 1000)

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.prepare(
      'INSERT INTO funding_rounds (id, tenant_id, title, matching_pool, starts_at, ends_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, tenant.id, body.title, body.matching_pool, now.toISOString(), end.toISOString()).run(),
    'DATABASE_ERROR',
    'Failed to create funding round'
  )

  return c.json({ id, matching_pool: body.matching_pool, ends_at: end.toISOString(), status: 'active' }, 201)
}))

// Add project to round
fundingRoutes.post('/projects', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: CreateProjectInput
  try {
    body = createProjectSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  // Edge case: Validate round exists and is active
  const round = await handleDb(
    () => c.env.DB.prepare('SELECT id, status FROM funding_rounds WHERE id = ? AND tenant_id = ?')
      .bind(body.round_id, tenant.id)
      .first(),
    'DATABASE_ERROR',
    'Failed to validate funding round'
  )

  if (!round) {
    return c.json(createError('NOT_FOUND', 'Funding round not found'), 404)
  }

  if ((round as { status: string }).status !== 'active') {
    return c.json(createError('CONFLICT', 'Funding round is not active'), 409)
  }

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.prepare(
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
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const id = crypto.randomUUID()
  try {
    await handleDb(
      () => c.env.DB.prepare(
        'INSERT INTO funding_contributions (id, project_id, stakeholder_id, amount) VALUES (?, ?, ?, ?)'
      ).bind(id, body.project_id, body.stakeholder_id, body.amount).run(),
      'DATABASE_ERROR',
      'Failed to record contribution'
    )
  } catch (error) {
    if (error instanceof Error && error.message.includes('UNIQUE')) {
      return c.json(createError('CONFLICT', 'Already contributed to this project'), 409)
    }
    console.error('Failed to record funding contribution:', { error, projectId: body.project_id })
    throw error
  }

  // Update project totals
  await handleDb(
    () => c.env.DB.prepare(
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
  const db = c.env.DB

  const round = await handleDb(
    () => db.prepare('SELECT * FROM funding_rounds WHERE id = ?').bind(roundId).first(),
    'DATABASE_ERROR',
    'Failed to fetch funding round'
  )
  if (!round) return c.json(createError('NOT_FOUND', 'Round not found'), 404)

  const projectsResult = await handleDb(
    async () => {
      const r = await db.prepare('SELECT * FROM funding_projects WHERE round_id = ?').bind(roundId).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch projects for round'
  )

  const results: any[] = []
  let totalQFScore = 0

  for (const project of projectsResult.results || []) {
    const contributionsResult = await handleDb(
      async () => {
        const r = await db.prepare(
          'SELECT amount FROM funding_contributions WHERE project_id = ?'
        ).bind(project.id).all()
        return r as { results?: any[] }
      },
      'DATABASE_ERROR',
      `Failed to fetch contributions for project ${project.id}`
    )

    // QF formula: matched = (Σ√ci)² - Σci
    const sqrtSum = (contributionsResult.results || []).reduce((sum: number, c: any) => sum + Math.sqrt(c.amount), 0)
    const directSum = (contributionsResult.results || []).reduce((sum: number, c: any) => sum + c.amount, 0)
    const qfScore = Math.pow(sqrtSum, 2) - directSum

    results.push({ id: project.id, name: project.name, direct: directSum, qf_score: qfScore, contributors: contributionsResult.results?.length || 0, matched_amount: 0, total: 0 })
    totalQFScore += Math.max(0, qfScore)
  }

  // Distribute matching pool proportionally to QF scores
  const matchingPool = (round as any).matching_pool
  for (const r of results) {
    r.matched_amount = totalQFScore > 0 ? Math.floor((r.qf_score / totalQFScore) * matchingPool) : 0
    r.total = r.direct + r.matched_amount

    await handleDb(
      () => db.prepare('UPDATE funding_projects SET matched_amount = ? WHERE id = ?').bind(r.matched_amount, r.id).run(),
      'DATABASE_ERROR',
      `Failed to update matched amount for project ${r.id}`
    )
  }

  await handleDb(
    () => db.prepare("UPDATE funding_rounds SET status = 'completed' WHERE id = ?").bind(roundId).run(),
    'DATABASE_ERROR',
    'Failed to update round status to completed'
  )

  return c.json({
    round_id: roundId,
    matching_pool: matchingPool,
    results: results.sort((a: any, b: any) => b.total - a.total),
    note: 'QF: 10 people × $1 beats 1 person × $10 — democratic funding'
  })
}))

// List rounds
fundingRoutes.get('/rounds', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

  await handleDb(
    () => ensureFundingTables(c.env.DB),
    'DATABASE_ERROR',
    'Failed to ensure funding tables exist'
  )
  const rowsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare('SELECT * FROM funding_rounds WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?').bind(tenant.id, limit).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch funding rounds'
  )
  return c.json({ rounds: rowsResult.results, count: rowsResult.results?.length || 0 })
}))

export { fundingRoutes }
