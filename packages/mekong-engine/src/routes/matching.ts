import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { createError, handleAsync, handleDb } from '../types/error'

type Variables = { tenant: Tenant }

// Zod schemas for matching operations
const createProfileSchema = z.object({
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  skills: z.array(z.string()).optional(),
  industries: z.array(z.string()).optional(),
  availability: z.string().optional().default('available'),
  hourly_rate_usd: z.number().positive('hourly_rate_usd must be positive').optional(),
  bio: z.string().optional(),
})

const createRequestSchema = z.object({
  requester_id: z.string().uuid('requester_id must be a valid UUID'),
  request_type: z.enum(['expert_needed', 'cofounder_needed', 'mentor_needed', 'vc_intro']),
  skills_needed: z.array(z.string()).optional(),
  industry: z.string().optional(),
  description: z.string().optional(),
  budget_usd: z.number().positive('budget_usd must be positive').optional(),
})

const updateMatchSchema = z.object({
  status: z.enum(['accepted', 'rejected', 'completed']),
})

type CreateProfileBody = z.infer<typeof createProfileSchema>
type CreateRequestBody = z.infer<typeof createRequestSchema>
type UpdateMatchBody = z.infer<typeof updateMatchSchema>
const matchingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
matchingRoutes.use('*', authMiddleware)

// ─── SKILL PROFILES ───

// POST /profiles — upsert skill profile
matchingRoutes.post('/profiles', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: CreateProfileBody
  try {
    body = createProfileSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const stakeholder = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        'SELECT id FROM stakeholders WHERE id = ? AND tenant_id = ?'
      ).bind(body.stakeholder_id, tenant.id).first()
      return result as { id: string } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch stakeholder'
  )
  if (!stakeholder) return c.json(createError('NOT_FOUND', 'Stakeholder not found'), 404)

  const existingResult = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        'SELECT id FROM skill_profiles WHERE stakeholder_id = ?'
      ).bind(body.stakeholder_id).first()
      return result as { id: string } | null
    },
    'DATABASE_ERROR',
    'Failed to check existing profile'
  )

  const skills = JSON.stringify(body.skills || [])
  const industries = JSON.stringify(body.industries || [])
  const availability = body.availability || 'available'
  const now = new Date().toISOString()

  if (existingResult) {
    await handleDb(
      () => c.env.DB.prepare(
        `UPDATE skill_profiles SET skills = ?, industries = ?, availability = ?,
         hourly_rate_usd = ?, bio = ?, updated_at = ? WHERE stakeholder_id = ?`
      ).bind(skills, industries, availability, body.hourly_rate_usd ?? null,
        body.bio ?? null, now, body.stakeholder_id).run(),
      'DATABASE_ERROR',
      'Failed to update profile'
    )
    return c.json({ id: existingResult.id, updated: true })
  }

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO skill_profiles (id, stakeholder_id, tenant_id, skills, industries, availability, hourly_rate_usd, bio, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, body.stakeholder_id, tenant.id, skills, industries, availability,
      body.hourly_rate_usd ?? null, body.bio ?? null, now).run(),
    'DATABASE_ERROR',
    'Failed to create profile'
  )

  return c.json({ id, created: true }, 201)
}))

// ─── MATCH REQUESTS ───

// POST /requests — create match request + auto-match
matchingRoutes.post('/requests', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: CreateRequestBody
  try {
    body = createRequestSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const requestId = crypto.randomUUID()
  const skillsNeeded = body.skills_needed || []
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO match_requests (id, tenant_id, requester_id, request_type, skills_needed, industry, description, budget_usd)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(requestId, tenant.id, body.requester_id, body.request_type,
      JSON.stringify(skillsNeeded), body.industry ?? null, body.description ?? null,
      body.budget_usd ?? null).run(),
    'DATABASE_ERROR',
    'Failed to create match request'
  )

  // Auto-match: find available profiles in same tenant
  const profilesResult = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        `SELECT sp.*, s.reputation_score FROM skill_profiles sp
         JOIN stakeholders s ON s.id = sp.stakeholder_id
         WHERE sp.tenant_id = ? AND sp.stakeholder_id != ? AND sp.availability = 'available'`
      ).bind(tenant.id, body.requester_id).all()
      return result as { results?: Array<{ stakeholder_id: string; skills: string; industries: string; reputation_score: number }> }
    },
    'DATABASE_ERROR',
    'Failed to fetch profiles for matching'
  )

  const proposedMatches = []

  for (const profile of profilesResult.results || []) {
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
    await handleDb(
      () => c.env.DB.prepare(
        `INSERT INTO matches (id, request_id, matched_stakeholder_id, match_score, match_reasons)
         VALUES (?, ?, ?, ?, ?)`
      ).bind(matchId, requestId, profile.stakeholder_id, totalScore, JSON.stringify(reasons)).run(),
      'DATABASE_ERROR',
      'Failed to create match'
    )

    proposedMatches.push({
      match_id: matchId,
      stakeholder_id: profile.stakeholder_id,
      score: parseFloat(totalScore.toFixed(3)),
      reasons,
    })
  }

  // Update request status if matches found
  if (proposedMatches.length > 0) {
    await handleDb(
      () => c.env.DB.prepare(
        "UPDATE match_requests SET status = 'matched' WHERE id = ?"
      ).bind(requestId).run(),
      'DATABASE_ERROR',
      'Failed to update request status'
    )
  }

  return c.json({
    request_id: requestId,
    matches_found: proposedMatches.length,
    matches: proposedMatches.sort((a, b) => b.score - a.score).slice(0, 5),
  }, 201)
}))

// PATCH /matches/:id — accept or reject match
matchingRoutes.patch('/matches/:id', handleAsync(async (c) => {
  const id = c.req.param('id')

  let body: UpdateMatchBody
  try {
    body = updateMatchSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const match = await handleDb(
    () => c.env.DB.prepare('SELECT * FROM matches WHERE id = ?').bind(id).first(),
    'DATABASE_ERROR',
    'Failed to fetch match'
  )
  if (!match) return c.json(createError('NOT_FOUND', 'Match not found'), 404)

  await handleDb(
    () => c.env.DB.prepare('UPDATE matches SET status = ? WHERE id = ?').bind(body.status, id).run(),
    'DATABASE_ERROR',
    'Failed to update match status'
  )

  return c.json({ id, status: body.status })
}))

// GET /requests — list all match requests
matchingRoutes.get('/requests', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const status = c.req.query('status')

  const query = status
    ? 'SELECT * FROM match_requests WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM match_requests WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rowsResult = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(query).bind(...params).all()
      return result as { results?: unknown[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch match requests'
  )

  return c.json({ requests: rowsResult.results, total: rowsResult.results?.length || 0 })
}))

export { matchingRoutes }
