import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { GOVERNANCE_VOICE_CREDITS } from '../types/raas'
import { z } from 'zod'

type Variables = { tenant: Tenant }
const governanceRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
governanceRoutes.use('*', authMiddleware)

// ─── ZOD SCHEMAS FOR VALIDATION ───

const stakeholderSchema = z.object({
  display_name: z.string().min(1, 'Display name is required'),
  email: z.string().email().optional().or(z.literal('')),
  role: z.enum([
    'owner', 'admin', 'operator', 'vc_partner',
    'founder', 'expert', 'developer', 'customer', 'community'
  ]).optional(),
})

const proposalSchema = z.object({
  author_id: z.string().uuid('Invalid author_id format'),
  title: z.string().min(1, 'Title is required'),
  body: z.string().min(1, 'Body is required'),
  proposal_type: z.enum(['feature', 'strategic', 'constitutional', 'treasury', 'equity']).optional(),
  voting_mechanism: z.enum(['quadratic', 'simple_majority', 'supermajority']).optional(),
  voting_days: z.number().int().positive().max(30).optional(),
})

const voteSchema = z.object({
  proposal_id: z.string().uuid('Invalid proposal_id format'),
  stakeholder_id: z.string().uuid('Invalid stakeholder_id format'),
  voice_credits: z.number().int().positive('Voice credits must be positive'),
  direction: z.enum(['for', 'against', 'abstain']).optional(),
})

const reputationSchema = z.object({
  stakeholder_id: z.string().uuid('Invalid stakeholder_id format'),
  dimension: z.enum(['code', 'mentorship', 'governance', 'expertise', 'community', 'general']).optional(),
  points: z.number().int().min(-100).max(100),
  reason: z.string().min(1, 'Reason is required'),
})

const nguSuSchema = z.object({
  entity_name: z.string().min(1, 'Entity name is required'),
  dao: z.number().min(0).max(5),
  thien: z.number().min(0).max(5),
  dia: z.number().min(0).max(5),
  tuong: z.number().min(0).max(5),
  phap: z.number().min(0).max(5),
  terrain: z.string().optional(),
  notes: z.string().optional(),
})

// ─── STAKEHOLDERS ───

// Register stakeholder
governanceRoutes.post('/stakeholders', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const tenant = c.get('tenant')

  let body
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body', code: 'BAD_REQUEST' }, 400)
  }

  const parsed = stakeholderSchema.safeParse(body)
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  const role = parsed.data.role || 'community'
  const levelMap: Record<string, number> = {
    owner: 1, admin: 2, operator: 3, vc_partner: 4,
    founder: 5, expert: 5, developer: 6, customer: 6, community: 6
  }
  const voiceCredits = GOVERNANCE_VOICE_CREDITS[role] || 10

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO stakeholders (id, tenant_id, display_name, email, role, governance_level, voice_credits_monthly) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(id, tenant.id, parsed.data.display_name, parsed.data.email || null, role, levelMap[role] || 6, voiceCredits).run()

  return c.json({
    id,
    role,
    governance_level: levelMap[role],
    voice_credits: voiceCredits,
    message: 'Stakeholder registered successfully'
  }, 201)
})

// List stakeholders
governanceRoutes.get('/stakeholders', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const role = c.req.query('role')
  const query = role
    ? 'SELECT * FROM stakeholders WHERE tenant_id = ? AND role = ? ORDER BY governance_level DESC, reputation_score DESC'
    : 'SELECT * FROM stakeholders WHERE tenant_id = ? ORDER BY governance_level DESC, reputation_score DESC'
  const params = role ? [tenant.id, role] : [tenant.id]
  const rows = await c.env.DB.prepare(query).bind(...params).all()
  return c.json({ stakeholders: rows.results, total: rows.results?.length || 0 })
})

// ─── PROPOSALS ───

// Create proposal
governanceRoutes.post('/proposals', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const tenant = c.get('tenant')

  let body
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body', code: 'BAD_REQUEST' }, 400)
  }

  const parsed = proposalSchema.safeParse(body)
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  // Constitutional proposals need supermajority (75%)
  const proposalType = parsed.data.proposal_type || 'feature'
  const mechanism = proposalType === 'constitutional' ? 'supermajority' : (parsed.data.voting_mechanism || 'quadratic')
  const quorum = proposalType === 'constitutional' ? 0.75 : 0.10

  const now = new Date()
  const votingDays = parsed.data.voting_days || 7
  const votingEnd = new Date(now.getTime() + votingDays * 24 * 60 * 60 * 1000)

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO proposals (id, tenant_id, author_id, title, body, proposal_type, voting_mechanism, status, quorum_pct, voting_starts_at, voting_ends_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'voting', ?, ?, ?)`
  ).bind(id, tenant.id, parsed.data.author_id, parsed.data.title, parsed.data.body, proposalType, mechanism, quorum,
    now.toISOString(), votingEnd.toISOString()).run()

  return c.json({
    id,
    proposal_type: proposalType,
    mechanism,
    quorum,
    voting_ends_at: votingEnd.toISOString(),
    message: 'Proposal created successfully'
  }, 201)
})

// List proposals
governanceRoutes.get('/proposals', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const status = c.req.query('status')
  const query = status
    ? 'SELECT * FROM proposals WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM proposals WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rows = await c.env.DB.prepare(query).bind(...params).all()

  // Enrich with vote counts
  const proposals = []
  for (const p of rows.results || []) {
    const voteStats = await c.env.DB.prepare(
      `SELECT direction, COUNT(*) as count, SUM(votes_cast) as total_votes
       FROM votes WHERE proposal_id = ? GROUP BY direction`
    ).bind(p.id).all()
    proposals.push({ ...p, vote_stats: voteStats.results })
  }

  return c.json({ proposals })
})

// ─── VOTING (Quadratic) ───

// Cast vote: cost = credits², votes = √credits
governanceRoutes.post('/vote', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const tenant = c.get('tenant')

  let body
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body', code: 'BAD_REQUEST' }, 400)
  }

  const parsed = voteSchema.safeParse(body)
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  // Check proposal is in voting state
  const proposal = await c.env.DB.prepare(
    'SELECT * FROM proposals WHERE id = ? AND tenant_id = ? AND status = ?'
  ).bind(parsed.data.proposal_id, tenant.id, 'voting').first()
  if (!proposal) return c.json({ error: 'Proposal not found or not in voting state', code: 'NOT_FOUND' }, 404)

  // Check voting deadline
  if (proposal.voting_ends_at && new Date(proposal.voting_ends_at as string) < new Date()) {
    return c.json({ error: 'Voting period has ended', code: 'VOTING_CLOSED' }, 400)
  }

  // Check stakeholder exists and has enough credits
  const stakeholder = await c.env.DB.prepare(
    'SELECT * FROM stakeholders WHERE id = ? AND tenant_id = ?'
  ).bind(parsed.data.stakeholder_id, tenant.id).first()
  if (!stakeholder) return c.json({ error: 'Stakeholder not found', code: 'NOT_FOUND' }, 404)

  // QV: votes = √(credits spent), cost = credits²
  const creditsSpent = Math.abs(parsed.data.voice_credits)
  const votesCast = Math.sqrt(creditsSpent)
  const direction = parsed.data.direction || 'for'

  const id = crypto.randomUUID()
  try {
    await c.env.DB.prepare(
      'INSERT INTO votes (id, proposal_id, stakeholder_id, voice_credits_spent, votes_cast, direction) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, parsed.data.proposal_id, parsed.data.stakeholder_id, creditsSpent, votesCast, direction).run()
  } catch (e: any) {
    if (e.message?.includes('UNIQUE')) return c.json({ error: 'Already voted on this proposal', code: 'CONFLICT' }, 409)
    throw e
  }

  // Update proposal voice_credits_pool
  await c.env.DB.prepare(
    'UPDATE proposals SET voice_credits_pool = voice_credits_pool + ? WHERE id = ?'
  ).bind(creditsSpent, parsed.data.proposal_id).run()

  return c.json({
    vote_id: id,
    credits_spent: creditsSpent,
    votes_cast: votesCast.toFixed(2),
    direction,
    message: `QV: ${creditsSpent} credits → ${votesCast.toFixed(2)} votes`
  }, 201)
})

// ─── REPUTATION ───

// Add reputation event
governanceRoutes.post('/reputation', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const tenant = c.get('tenant')

  let body
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body', code: 'BAD_REQUEST' }, 400)
  }

  const parsed = reputationSchema.safeParse(body)
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  await c.env.DB.prepare(
    'INSERT INTO reputation_events (stakeholder_id, tenant_id, dimension, points_delta, reason) VALUES (?, ?, ?, ?, ?)'
  ).bind(parsed.data.stakeholder_id, tenant.id, parsed.data.dimension || 'general', parsed.data.points, parsed.data.reason).run()

  // Update stakeholder total
  await c.env.DB.prepare(
    'UPDATE stakeholders SET reputation_score = reputation_score + ? WHERE id = ? AND tenant_id = ?'
  ).bind(parsed.data.points, parsed.data.stakeholder_id, tenant.id).run()

  return c.json({ added: parsed.data.points, dimension: parsed.data.dimension || 'general' }, 201)
})

// Get reputation leaderboard
governanceRoutes.get('/reputation', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const rows = await c.env.DB.prepare(
    'SELECT id, display_name, role, reputation_score, governance_level FROM stakeholders WHERE tenant_id = ? ORDER BY reputation_score DESC LIMIT 20'
  ).bind(tenant.id).all()
  return c.json({ leaderboard: rows.results })
})

// ─── NGŨ SỰ SCORES ───

// Score a portfolio entity
governanceRoutes.post('/ngu-su', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const tenant = c.get('tenant')

  let body
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body', code: 'BAD_REQUEST' }, 400)
  }

  const parsed = nguSuSchema.safeParse(body)
  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
  }

  // Auto-classify terrain based on scores
  const overall = (parsed.data.dao + parsed.data.thien + parsed.data.dia + parsed.data.tuong + parsed.data.phap) / 5
  let terrain = parsed.data.terrain || 'unknown'
  if (terrain === 'unknown') {
    if (overall < 1.5) terrain = 'tu_dia'       // Death ground
    else if (overall < 2.5) terrain = 'vi_dia'   // Hemmed-in
    else if (overall < 3.5) terrain = 'tranh_dia' // Contentious
    else terrain = 'giao_dia'                     // Intersecting
  }

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO ngu_su_scores (id, tenant_id, entity_name, dao_score, thien_score, dia_score, tuong_score, phap_score, terrain, notes)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenant.id, parsed.data.entity_name, parsed.data.dao, parsed.data.thien, parsed.data.dia, parsed.data.tuong, parsed.data.phap, terrain, parsed.data.notes || null).run()

  return c.json({ id, overall: overall.toFixed(2), terrain }, 201)
})

// List scores
governanceRoutes.get('/ngu-su', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const rows = await c.env.DB.prepare(
    'SELECT * FROM ngu_su_scores WHERE tenant_id = ? ORDER BY scored_at DESC'
  ).bind(tenant.id).all()
  return c.json({ scores: rows.results })
})

// ─── TREASURY ───

governanceRoutes.get('/treasury', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  let treasury = await c.env.DB.prepare('SELECT * FROM treasury WHERE tenant_id = ?').bind(tenant.id).first()
  if (!treasury) {
    const id = crypto.randomUUID()
    await c.env.DB.prepare('INSERT INTO treasury (id, tenant_id) VALUES (?, ?)').bind(id, tenant.id).run()
    treasury = { id, tenant_id: tenant.id, balance: 0, total_in: 0, total_out: 0 }
  }
  return c.json(treasury)
})

export { governanceRoutes }
