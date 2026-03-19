import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { GOVERNANCE_VOICE_CREDITS } from '../types/raas'

type Variables = { tenant: Tenant }
const governanceRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
governanceRoutes.use('*', authMiddleware)

// ─── STAKEHOLDERS ───

// Register stakeholder
governanceRoutes.post('/stakeholders', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    display_name: string; email?: string; role?: string
  }>()
  if (!body.display_name?.trim()) return c.json({ error: 'Missing display_name' }, 400)

  const role = body.role || 'community'
  const validRoles = ['owner','admin','operator','vc_partner','founder','expert','developer','customer','community']
  if (!validRoles.includes(role)) return c.json({ error: `Invalid role. Valid: ${validRoles.join(', ')}` }, 400)

  // Governance level: tam giác ngược — community=6 (most power), owner=1 (least)
  const levelMap: Record<string, number> = {
    owner: 1, admin: 2, operator: 3, vc_partner: 4,
    founder: 5, expert: 5, developer: 6, customer: 6, community: 6
  }
  const voiceCredits = GOVERNANCE_VOICE_CREDITS[role] || 10

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO stakeholders (id, tenant_id, display_name, email, role, governance_level, voice_credits_monthly) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(id, tenant.id, body.display_name, body.email || null, role, levelMap[role] || 6, voiceCredits).run()

  return c.json({ id, role, governance_level: levelMap[role], voice_credits: voiceCredits }, 201)
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
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    author_id: string; title: string; body: string;
    proposal_type?: string; voting_mechanism?: string;
    voting_days?: number
  }>()

  if (!body.title?.trim() || !body.body?.trim()) return c.json({ error: 'Missing title or body' }, 400)

  // Constitutional proposals need supermajority (75%)
  const proposalType = body.proposal_type || 'feature'
  const mechanism = proposalType === 'constitutional' ? 'supermajority' : (body.voting_mechanism || 'quadratic')
  const quorum = proposalType === 'constitutional' ? 0.75 : 0.10

  const now = new Date()
  const votingDays = body.voting_days || 7
  const votingEnd = new Date(now.getTime() + votingDays * 24 * 60 * 60 * 1000)

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO proposals (id, tenant_id, author_id, title, body, proposal_type, voting_mechanism, status, quorum_pct, voting_starts_at, voting_ends_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'voting', ?, ?, ?)`
  ).bind(id, tenant.id, body.author_id, body.title, body.body, proposalType, mechanism, quorum,
    now.toISOString(), votingEnd.toISOString()).run()

  return c.json({ id, proposal_type: proposalType, mechanism, quorum, voting_ends_at: votingEnd.toISOString() }, 201)
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
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    proposal_id: string; stakeholder_id: string;
    voice_credits: number; direction?: string
  }>()

  if (!body.proposal_id || !body.stakeholder_id || !body.voice_credits) {
    return c.json({ error: 'Missing proposal_id, stakeholder_id, or voice_credits' }, 400)
  }

  // Check proposal is in voting state
  const proposal = await c.env.DB.prepare(
    'SELECT * FROM proposals WHERE id = ? AND tenant_id = ? AND status = ?'
  ).bind(body.proposal_id, tenant.id, 'voting').first()
  if (!proposal) return c.json({ error: 'Proposal not found or not in voting state' }, 404)

  // Check voting deadline
  if (proposal.voting_ends_at && new Date(proposal.voting_ends_at as string) < new Date()) {
    return c.json({ error: 'Voting period has ended' }, 400)
  }

  // Check stakeholder exists and has enough credits
  const stakeholder = await c.env.DB.prepare(
    'SELECT * FROM stakeholders WHERE id = ? AND tenant_id = ?'
  ).bind(body.stakeholder_id, tenant.id).first()
  if (!stakeholder) return c.json({ error: 'Stakeholder not found' }, 404)

  // QV: votes = √(credits spent), cost = credits²
  const creditsSpent = Math.abs(body.voice_credits)
  const votesCast = Math.sqrt(creditsSpent)
  const direction = body.direction || 'for'

  const id = crypto.randomUUID()
  try {
    await c.env.DB.prepare(
      'INSERT INTO votes (id, proposal_id, stakeholder_id, voice_credits_spent, votes_cast, direction) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, body.proposal_id, body.stakeholder_id, creditsSpent, votesCast, direction).run()
  } catch (e: any) {
    if (e.message?.includes('UNIQUE')) return c.json({ error: 'Already voted on this proposal' }, 409)
    throw e
  }

  // Update proposal voice_credits_pool
  await c.env.DB.prepare(
    'UPDATE proposals SET voice_credits_pool = voice_credits_pool + ? WHERE id = ?'
  ).bind(creditsSpent, body.proposal_id).run()

  return c.json({
    vote_id: id, credits_spent: creditsSpent, votes_cast: votesCast.toFixed(2),
    direction, message: `QV: ${creditsSpent} credits → ${votesCast.toFixed(2)} votes`
  }, 201)
})

// ─── REPUTATION ───

// Add reputation event
governanceRoutes.post('/reputation', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    stakeholder_id: string; dimension?: string; points: number; reason: string
  }>()

  await c.env.DB.prepare(
    'INSERT INTO reputation_events (stakeholder_id, tenant_id, dimension, points_delta, reason) VALUES (?, ?, ?, ?, ?)'
  ).bind(body.stakeholder_id, tenant.id, body.dimension || 'general', body.points, body.reason).run()

  // Update stakeholder total
  await c.env.DB.prepare(
    'UPDATE stakeholders SET reputation_score = reputation_score + ? WHERE id = ? AND tenant_id = ?'
  ).bind(body.points, body.stakeholder_id, tenant.id).run()

  return c.json({ added: body.points, dimension: body.dimension || 'general' }, 201)
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
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    entity_name: string; dao: number; thien: number; dia: number; tuong: number; phap: number;
    terrain?: string; notes?: string
  }>()

  // Auto-classify terrain based on scores
  const overall = (body.dao + body.thien + body.dia + body.tuong + body.phap) / 5
  let terrain = body.terrain || 'unknown'
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
  ).bind(id, tenant.id, body.entity_name, body.dao, body.thien, body.dia, body.tuong, body.phap, terrain, body.notes || null).run()

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
