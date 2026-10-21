import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { GOVERNANCE_VOICE_CREDITS } from '../types/raas'
import { handleAsync, handleDb } from '../types/error'
import { autoClassifyFromDB } from '../raas/terrain-classifier'
import {
  type DbResult,
  type StakeholderRow,
  GOVERNANCE_ROLE_LEVELS,
  stakeholderSchema,
  proposalSchema,
  voteSchema,
  reputationSchema,
  nguSuSchema,
  classifyNguSuTerrain,
} from './governance-schemas'
import { registerProposalAndVoteRoutes } from './governance-proposal-vote-handlers'

type Variables = { tenant: Tenant }
const governanceRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
governanceRoutes.use('*', authMiddleware)

// ─── STAKEHOLDERS ───

governanceRoutes.post('/stakeholders', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const parsed = stakeholderSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  const role = parsed.data.role || 'community'
  const voiceCredits = GOVERNANCE_VOICE_CREDITS[role] || 10
  const id = crypto.randomUUID()

  await handleDb(
    () => c.env.DB!.prepare(
      'INSERT INTO stakeholders (id, tenant_id, display_name, email, role, governance_level, voice_credits_monthly) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(id, tenant.id, parsed.data.display_name, parsed.data.email || null, role, GOVERNANCE_ROLE_LEVELS[role] || 6, voiceCredits).run(),
    'DATABASE_ERROR',
    'Failed to register stakeholder'
  )

  return c.json({
    id,
    role,
    governance_level: GOVERNANCE_ROLE_LEVELS[role],
    voice_credits: voiceCredits,
    message: 'Stakeholder registered successfully',
  }, 201)
}))

governanceRoutes.get('/stakeholders', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const role = c.req.query('role')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)
  const query = role
    ? 'SELECT * FROM stakeholders WHERE tenant_id = ? AND role = ? ORDER BY governance_level DESC, reputation_score DESC LIMIT ?'
    : 'SELECT * FROM stakeholders WHERE tenant_id = ? ORDER BY governance_level DESC, reputation_score DESC LIMIT ?'
  const params = role ? [tenant.id, role, limit] : [tenant.id, limit]
  const rowsResult = await handleDb(
    async () => (await c.env.DB!.prepare(query).bind(...params).all()) as unknown as DbResult<StakeholderRow>,
    'DATABASE_ERROR',
    'Failed to fetch stakeholders'
  )
  return c.json({ stakeholders: rowsResult.results, total: rowsResult.results?.length || 0 })
}))

// ─── PROPOSALS & VOTING (Quadratic) ───

registerProposalAndVoteRoutes(governanceRoutes)

// ─── REPUTATION ───

governanceRoutes.post('/reputation', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const parsed = reputationSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  await handleDb(
    () => c.env.DB!.prepare(
      'INSERT INTO reputation_events (stakeholder_id, tenant_id, dimension, points_delta, reason) VALUES (?, ?, ?, ?, ?)'
    ).bind(parsed.data.stakeholder_id, tenant.id, parsed.data.dimension || 'general', parsed.data.points, parsed.data.reason).run(),
    'DATABASE_ERROR',
    'Failed to add reputation event'
  )

  await handleDb(
    () => c.env.DB!.prepare(
      'UPDATE stakeholders SET reputation_score = reputation_score + ? WHERE id = ? AND tenant_id = ?'
    ).bind(parsed.data.points, parsed.data.stakeholder_id, tenant.id).run(),
    'DATABASE_ERROR',
    'Failed to update reputation score'
  )

  return c.json({ added: parsed.data.points, dimension: parsed.data.dimension || 'general' }, 201)
}))

governanceRoutes.get('/reputation', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const rowsResult = await handleDb(
    async () => (await c.env.DB!.prepare(
      'SELECT id, display_name, role, reputation_score, governance_level FROM stakeholders WHERE tenant_id = ? ORDER BY reputation_score DESC LIMIT 20'
    ).bind(tenant.id).all()) as unknown as DbResult<StakeholderRow>,
    'DATABASE_ERROR',
    'Failed to fetch reputation leaderboard'
  )
  return c.json({ leaderboard: rowsResult.results })
}))

// ─── NGŨ SỰ SCORES ───

governanceRoutes.post('/ngu-su', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const parsed = nguSuSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  const overall = (parsed.data.dao + parsed.data.thien + parsed.data.dia + parsed.data.tuong + parsed.data.phap) / 5
  const terrain = classifyNguSuTerrain(overall, parsed.data.terrain)
  const id = crypto.randomUUID()

  await handleDb(
    () => c.env.DB!.prepare(
      `INSERT INTO ngu_su_scores (id, tenant_id, entity_name, dao_score, thien_score, dia_score, tuong_score, phap_score, terrain, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenant.id, parsed.data.entity_name, parsed.data.dao, parsed.data.thien, parsed.data.dia, parsed.data.tuong, parsed.data.phap, terrain, parsed.data.notes || null).run(),
    'DATABASE_ERROR',
    'Failed to score entity'
  )

  return c.json({ id, overall: overall.toFixed(2), terrain }, 201)
}))

governanceRoutes.get('/ngu-su', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const rowsResult = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM ngu_su_scores WHERE tenant_id = ? ORDER BY scored_at DESC').bind(tenant.id).all()) as unknown as DbResult,
    'DATABASE_ERROR',
    'Failed to fetch scores'
  )
  return c.json({ scores: rowsResult.results })
}))

// ─── TREASURY & TERRAIN AUTO-CLASSIFY ───

governanceRoutes.get('/treasury', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  let treasury = await handleDb(
    () => c.env.DB!.prepare('SELECT * FROM treasury WHERE tenant_id = ?').bind(tenant.id).first(),
    'DATABASE_ERROR',
    'Failed to fetch treasury'
  )
  if (!treasury) {
    const id = crypto.randomUUID()
    await handleDb(
      () => c.env.DB!.prepare('INSERT INTO treasury (id, tenant_id) VALUES (?, ?)').bind(id, tenant.id).run(),
      'DATABASE_ERROR',
      'Failed to initialize treasury'
    )
    treasury = { id, tenant_id: tenant.id, balance: 0, total_in: 0, total_out: 0 }
  }
  return c.json(treasury)
}))

governanceRoutes.get('/terrain-auto', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  return c.json(await autoClassifyFromDB(c.env.DB, tenant.id))
}))

export { governanceRoutes, stakeholderSchema, proposalSchema, voteSchema, reputationSchema, nguSuSchema }
