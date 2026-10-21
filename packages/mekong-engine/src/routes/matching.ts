import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { createError, handleAsync, handleDb } from '../types/error'
import {
  type CreateProfileBody,
  type CreateRequestBody,
  type UpdateMatchBody,
  type CandidateProfileRow,
  type ProposedMatch,
  createProfileSchema,
  createRequestSchema,
  updateMatchSchema,
  evaluateCandidateProfile,
} from './matching-schemas'

type Variables = { tenant: Tenant }
const matchingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
matchingRoutes.use('*', authMiddleware)

// ─── SKILL PROFILES ───

matchingRoutes.post('/profiles', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  let body: CreateProfileBody
  try {
    body = createProfileSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const stakeholder = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT id FROM stakeholders WHERE id = ? AND tenant_id = ?').bind(body.stakeholder_id, tenant.id).first()) as { id: string } | null,
    'DATABASE_ERROR',
    'Failed to fetch stakeholder'
  )
  if (!stakeholder) return c.json(createError('NOT_FOUND', 'Stakeholder not found'), 404)

  const existingResult = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT id FROM skill_profiles WHERE stakeholder_id = ?').bind(body.stakeholder_id).first()) as { id: string } | null,
    'DATABASE_ERROR',
    'Failed to check existing profile'
  )

  const skills = JSON.stringify(body.skills || [])
  const industries = JSON.stringify(body.industries || [])
  const availability = body.availability || 'available'
  const now = new Date().toISOString()

  if (existingResult) {
    await handleDb(
      () => c.env.DB!.prepare(
        `UPDATE skill_profiles SET skills = ?, industries = ?, availability = ?, hourly_rate_usd = ?, bio = ?, updated_at = ? WHERE stakeholder_id = ?`
      ).bind(skills, industries, availability, body.hourly_rate_usd ?? null, body.bio ?? null, now, body.stakeholder_id).run(),
      'DATABASE_ERROR',
      'Failed to update profile'
    )
    return c.json({ id: existingResult.id, updated: true })
  }

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB!.prepare(
      `INSERT INTO skill_profiles (id, stakeholder_id, tenant_id, skills, industries, availability, hourly_rate_usd, bio, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, body.stakeholder_id, tenant.id, skills, industries, availability, body.hourly_rate_usd ?? null, body.bio ?? null, now).run(),
    'DATABASE_ERROR',
    'Failed to create profile'
  )

  return c.json({ id, created: true }, 201)
}))

// ─── MATCH REQUESTS ───

matchingRoutes.post('/requests', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  let body: CreateRequestBody
  try {
    body = createRequestSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const requestId = crypto.randomUUID()
  const skillsNeeded = body.skills_needed || []
  await handleDb(
    () => c.env.DB!.prepare(
      `INSERT INTO match_requests (id, tenant_id, requester_id, request_type, skills_needed, industry, description, budget_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(requestId, tenant.id, body.requester_id, body.request_type, JSON.stringify(skillsNeeded), body.industry ?? null, body.description ?? null, body.budget_usd ?? null).run(),
    'DATABASE_ERROR',
    'Failed to create match request'
  )

  const profilesResult = await handleDb(
    async () => (await c.env.DB!.prepare(
      `SELECT sp.*, s.reputation_score FROM skill_profiles sp
       JOIN stakeholders s ON s.id = sp.stakeholder_id
       WHERE sp.tenant_id = ? AND sp.stakeholder_id != ? AND sp.availability = 'available'`
    ).bind(tenant.id, body.requester_id).all()) as unknown as CandidateProfileRow[],
    'DATABASE_ERROR',
    'Failed to fetch profiles for matching'
  )

  const proposedMatches: ProposedMatch[] = []
  for (const profile of profilesResult || []) {
    const evaluated = evaluateCandidateProfile(profile, skillsNeeded, body.industry)
    if (!evaluated) continue

    const matchId = crypto.randomUUID()
    await handleDb(
      () => c.env.DB!.prepare(
        `INSERT INTO matches (id, request_id, matched_stakeholder_id, match_score, match_reasons) VALUES (?, ?, ?, ?, ?)`
      ).bind(matchId, requestId, profile.stakeholder_id, evaluated.totalScore, JSON.stringify(evaluated.reasons)).run(),
      'DATABASE_ERROR',
      'Failed to create match'
    )

    proposedMatches.push({
      match_id: matchId,
      stakeholder_id: profile.stakeholder_id,
      score: parseFloat(evaluated.totalScore.toFixed(3)),
      reasons: evaluated.reasons,
    })
  }

  if (proposedMatches.length > 0) {
    await handleDb(
      () => c.env.DB!.prepare("UPDATE match_requests SET status = 'matched' WHERE id = ?").bind(requestId).run(),
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
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Invalid payload', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const match = await handleDb(() => c.env.DB!.prepare('SELECT * FROM matches WHERE id = ?').bind(id).first(), 'DATABASE_ERROR', 'Failed to fetch match')
  if (!match) return c.json(createError('NOT_FOUND', 'Match not found'), 404)

  await handleDb(() => c.env.DB!.prepare('UPDATE matches SET status = ? WHERE id = ?').bind(body.status, id).run(), 'DATABASE_ERROR', 'Failed to update match status')
  return c.json({ id, status: body.status })
}))

// GET /requests — list all match requests
matchingRoutes.get('/requests', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const status = c.req.query('status')
  const query = status
    ? 'SELECT * FROM match_requests WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM match_requests WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rowsResult = await handleDb(async () => c.env.DB!.prepare(query).bind(...params).all(), 'DATABASE_ERROR', 'Failed to fetch match requests')
  return c.json({ requests: rowsResult.results, total: rowsResult.results?.length || 0 })
}))

export { matchingRoutes, createProfileSchema, createRequestSchema, updateMatchSchema }
