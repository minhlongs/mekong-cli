import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'

type Variables = { tenant: Tenant }
const matchingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
matchingRoutes.use('*', authMiddleware)

// ─── SKILL PROFILES ───

// POST /profiles — upsert skill profile
matchingRoutes.post('/profiles', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: {
    stakeholder_id: string
    skills?: string[]
    industries?: string[]
    availability?: string
    hourly_rate_usd?: number
    bio?: string
  }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  if (!body.stakeholder_id) return c.json({ error: 'stakeholder_id required' }, 400)

  const stakeholder = await c.env.DB.prepare(
    'SELECT id FROM stakeholders WHERE id = ? AND tenant_id = ?'
  ).bind(body.stakeholder_id, tenant.id).first()
  if (!stakeholder) return c.json({ error: 'Stakeholder not found' }, 404)

  const existing = await c.env.DB.prepare(
    'SELECT id FROM skill_profiles WHERE stakeholder_id = ?'
  ).bind(body.stakeholder_id).first()

  const skills = JSON.stringify(body.skills || [])
  const industries = JSON.stringify(body.industries || [])
  const availability = body.availability || 'available'
  const now = new Date().toISOString()

  if (existing) {
    await c.env.DB.prepare(
      `UPDATE skill_profiles SET skills = ?, industries = ?, availability = ?,
       hourly_rate_usd = ?, bio = ?, updated_at = ? WHERE stakeholder_id = ?`
    ).bind(skills, industries, availability, body.hourly_rate_usd ?? null,
      body.bio ?? null, now, body.stakeholder_id).run()
    return c.json({ id: existing.id, updated: true })
  }

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO skill_profiles (id, stakeholder_id, tenant_id, skills, industries, availability, hourly_rate_usd, bio, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, body.stakeholder_id, tenant.id, skills, industries, availability,
    body.hourly_rate_usd ?? null, body.bio ?? null, now).run()

  return c.json({ id, created: true }, 201)
})

// ─── MATCH REQUESTS ───

// POST /requests — create match request + auto-match
matchingRoutes.post('/requests', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: {
    requester_id: string
    request_type: string
    skills_needed?: string[]
    industry?: string
    description?: string
    budget_usd?: number
  }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  if (!body.requester_id) return c.json({ error: 'requester_id required' }, 400)
  if (!body.request_type) return c.json({ error: 'request_type required' }, 400)

  const validTypes = ['expert_needed', 'cofounder_needed', 'mentor_needed', 'vc_intro']
  if (!validTypes.includes(body.request_type)) {
    return c.json({ error: `request_type must be one of: ${validTypes.join(', ')}` }, 400)
  }

  const requestId = crypto.randomUUID()
  const skillsNeeded = body.skills_needed || []
  await c.env.DB.prepare(
    `INSERT INTO match_requests (id, tenant_id, requester_id, request_type, skills_needed, industry, description, budget_usd)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(requestId, tenant.id, body.requester_id, body.request_type,
    JSON.stringify(skillsNeeded), body.industry ?? null, body.description ?? null,
    body.budget_usd ?? null).run()

  // Auto-match: find available profiles in same tenant
  const profiles = await c.env.DB.prepare(
    `SELECT sp.*, s.reputation_score FROM skill_profiles sp
     JOIN stakeholders s ON s.id = sp.stakeholder_id
     WHERE sp.tenant_id = ? AND sp.stakeholder_id != ? AND sp.availability = 'available'`
  ).bind(tenant.id, body.requester_id).all()

  const proposedMatches = []

  for (const profile of profiles.results || []) {
    const profileSkills: string[] = JSON.parse((profile.skills as string) || '[]')
    const profileIndustries: string[] = JSON.parse((profile.industries as string) || '[]')

    // Skill overlap score (60%)
    let skillScore = 0
    if (skillsNeeded.length > 0 && profileSkills.length > 0) {
      const overlap = skillsNeeded.filter(s =>
        profileSkills.some(ps => ps.toLowerCase() === s.toLowerCase())
      ).length
      skillScore = overlap / skillsNeeded.length
    } else if (skillsNeeded.length === 0) {
      skillScore = 1
    }

    // Industry match bonus
    const industryBonus = body.industry && profileIndustries.some(
      i => i.toLowerCase() === body.industry!.toLowerCase()
    ) ? 0.1 : 0

    // Reputation score (40%), normalized to 0-1 assuming max ~1000
    const reputationScore = Math.min((profile.reputation_score as number || 0) / 1000, 1)

    const totalScore = (skillScore + industryBonus) * 0.6 + reputationScore * 0.4
    if (totalScore < 0.1) continue

    const reasons: string[] = []
    if (skillScore > 0) reasons.push(`skill_overlap:${(skillScore * 100).toFixed(0)}%`)
    if (industryBonus > 0) reasons.push('industry_match')
    if (reputationScore > 0.3) reasons.push(`reputation:${(reputationScore * 100).toFixed(0)}`)

    const matchId = crypto.randomUUID()
    await c.env.DB.prepare(
      `INSERT INTO matches (id, request_id, matched_stakeholder_id, match_score, match_reasons)
       VALUES (?, ?, ?, ?, ?)`
    ).bind(matchId, requestId, profile.stakeholder_id, totalScore, JSON.stringify(reasons)).run()

    proposedMatches.push({
      match_id: matchId,
      stakeholder_id: profile.stakeholder_id,
      score: parseFloat(totalScore.toFixed(3)),
      reasons,
    })
  }

  // Update request status if matches found
  if (proposedMatches.length > 0) {
    await c.env.DB.prepare(
      "UPDATE match_requests SET status = 'matched' WHERE id = ?"
    ).bind(requestId).run()
  }

  return c.json({
    request_id: requestId,
    matches_found: proposedMatches.length,
    matches: proposedMatches.sort((a, b) => b.score - a.score).slice(0, 5),
  }, 201)
})

// PATCH /matches/:id — accept or reject match
matchingRoutes.patch('/matches/:id', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const id = c.req.param('id')

  let body: { status: string }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  const validStatuses = ['accepted', 'rejected', 'completed']
  if (!validStatuses.includes(body.status)) {
    return c.json({ error: `status must be one of: ${validStatuses.join(', ')}` }, 400)
  }

  const match = await c.env.DB.prepare('SELECT * FROM matches WHERE id = ?').bind(id).first()
  if (!match) return c.json({ error: 'Match not found' }, 404)

  await c.env.DB.prepare('UPDATE matches SET status = ? WHERE id = ?').bind(body.status, id).run()

  return c.json({ id, status: body.status })
})

// GET /requests — list all match requests
matchingRoutes.get('/requests', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const status = c.req.query('status')

  const query = status
    ? 'SELECT * FROM match_requests WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM match_requests WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rows = await c.env.DB.prepare(query).bind(...params).all()

  return c.json({ requests: rows.results, total: rows.results?.length || 0 })
})

export { matchingRoutes }
