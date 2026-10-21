import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync, handleDb, createError } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'
import {
  type CreateConflictBody,
  type EscalateConflictBody,
  type ResolveConflictBody,
  RESOLUTION_LEVELS,
  createConflictSchema,
  escalateConflictSchema,
  resolveConflictSchema,
  validTypes,
  validSeverities,
} from './conflicts-schemas'

type Variables = { tenant: Tenant }
const conflictRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
conflictRoutes.use('*', authMiddleware)

// POST / — report conflict
conflictRoutes.post('/', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant

  let body: CreateConflictBody
  try {
    body = createConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const startLevel = body.severity === 'critical' ? 3 : body.severity === 'high' ? 2 : 1
  const levelInfo = RESOLUTION_LEVELS[startLevel]!
  const id = crypto.randomUUID()

  await handleDb(
    () => c.env.DB!.prepare(
      `INSERT INTO conflicts (id, tenant_id, reporter_id, against_id, conflict_type, description, severity, resolution_level, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenant.id, body.reporter_id, body.against_id ?? null, body.conflict_type, body.description, body.severity, startLevel, 'open').run(),
    'DATABASE_ERROR',
    'Failed to create conflict record'
  )

  return c.json({
    id,
    severity: body.severity,
    resolution_level: startLevel,
    resolution_name: levelInfo.name,
    sla: levelInfo.sla,
    status: 'open',
    message: `Conflict reported. Resolution: ${levelInfo.name} (SLA: ${levelInfo.sla})`,
  }, 201)
}))

// POST /:id/escalate — increase resolution level
conflictRoutes.post('/:id/escalate', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant
  const id = c.req.param('id')

  let body: EscalateConflictBody
  try {
    body = escalateConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const conflict = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?').bind(id, tenant.id).first()) as { resolution_level: number; status: string } | null,
    'DATABASE_ERROR',
    'Failed to fetch conflict'
  )
  if (!conflict) return c.json(createError('NOT_FOUND', 'Conflict not found'), 404)

  const currentLevel = conflict.resolution_level
  if (currentLevel >= 5) {
    return c.json(createError('BAD_REQUEST', 'Already at maximum resolution level (constitutional review)'), 400)
  }
  if (['resolved', 'dismissed'].includes(conflict.status)) {
    return c.json(createError('BAD_REQUEST', 'Cannot escalate a resolved or dismissed conflict'), 400)
  }

  const newLevel = currentLevel + 1
  const levelInfo = RESOLUTION_LEVELS[newLevel]!

  await handleDb(
    () => c.env.DB!.prepare('UPDATE conflicts SET resolution_level = ?, status = ? WHERE id = ?').bind(newLevel, levelInfo.status, id).run(),
    'DATABASE_ERROR',
    'Failed to update conflict'
  )

  await handleDb(
    () => c.env.DB!.prepare(
      `INSERT INTO conflict_escalations (conflict_id, from_level, to_level, reason, escalated_by) VALUES (?, ?, ?, ?, ?)`
    ).bind(id, currentLevel, newLevel, body.reason, body.escalated_by ?? null).run(),
    'DATABASE_ERROR',
    'Failed to log escalation'
  )

  return c.json({
    id,
    from_level: currentLevel,
    to_level: newLevel,
    resolution_name: levelInfo.name,
    sla: levelInfo.sla,
    status: levelInfo.status,
    message: `Escalated to level ${newLevel}: ${levelInfo.name} (SLA: ${levelInfo.sla})`,
  })
}))

// POST /:id/resolve — close with notes
conflictRoutes.post('/:id/resolve', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant
  const id = c.req.param('id')

  let body: ResolveConflictBody
  try {
    body = resolveConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const conflict = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?').bind(id, tenant.id).first()) as { resolution_level: number; status: string } | null,
    'DATABASE_ERROR',
    'Failed to fetch conflict'
  )
  if (!conflict) return c.json(createError('NOT_FOUND', 'Conflict not found'), 404)

  const finalStatus = body.dismissed ? 'dismissed' : 'resolved'
  const now = new Date().toISOString()

  await handleDb(
    () => c.env.DB!.prepare('UPDATE conflicts SET status = ?, resolution_notes = ?, resolved_at = ? WHERE id = ?').bind(finalStatus, body.resolution_notes ?? null, now, id).run(),
    'DATABASE_ERROR',
    'Failed to resolve conflict'
  )

  return c.json({ id, status: finalStatus, resolved_at: now })
}))

// GET / — list conflicts by status
conflictRoutes.get('/', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant
  const status = c.req.query('status')
  const query = status
    ? 'SELECT * FROM conflicts WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM conflicts WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rows = await handleDb(
    async () => (await c.env.DB!.prepare(query).bind(...params).all()) as { results?: Record<string, unknown>[] },
    'DATABASE_ERROR',
    'Failed to fetch conflicts'
  )

  const conflicts = (rows.results || []).map((row) => ({
    ...row,
    resolution_info: RESOLUTION_LEVELS[(row.resolution_level as number) ?? 1] ?? null,
  }))

  return c.json({ conflicts, total: conflicts.length })
}))

export { conflictRoutes, RESOLUTION_LEVELS, validTypes, validSeverities, createConflictSchema, escalateConflictSchema, resolveConflictSchema }
