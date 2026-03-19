import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync, handleDb, requireResource, createError } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'

type Variables = { tenant: Tenant }

// Zod schemas for conflict operations
const validTypes = ['resource', 'equity', 'decision', 'conduct', 'constitutional'] as const
const validSeverities = ['low', 'medium', 'high', 'critical'] as const

const createConflictSchema = z.object({
  reporter_id: z.string().uuid('reporter_id must be a valid UUID'),
  against_id: z.string().uuid('against_id must be a valid UUID').optional(),
  conflict_type: z.enum([...validTypes] as [string, ...string[]]),
  description: z.string().min(1, 'description is required').max(2000, 'description must be ≤2000 chars'),
  severity: z.enum([...validSeverities] as [string, ...string[]]).optional().default('medium'),
})

const escalateConflictSchema = z.object({
  reason: z.string().min(1, 'reason is required').max(1000, 'reason must be ≤1000 chars'),
  escalated_by: z.string().uuid('escalated_by must be a valid UUID').optional(),
})

const resolveConflictSchema = z.object({
  resolution_notes: z.string().max(2000, 'resolution_notes must be ≤2000 chars').optional(),
  dismissed: z.boolean().optional().default(false),
})

type CreateConflictBody = z.infer<typeof createConflictSchema>
type EscalateConflictBody = z.infer<typeof escalateConflictSchema>
type ResolveConflictBody = z.infer<typeof resolveConflictSchema>

const conflictRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
conflictRoutes.use('*', authMiddleware)

// 5-level resolution protocol with SLA
export const RESOLUTION_LEVELS: Record<number, { name: string; sla: string; status: string }> = {
  1: { name: 'auto_resolve', sla: '1h', status: 'auto_resolved' },
  2: { name: 'agent_negotiation', sla: '4h', status: 'negotiating' },
  3: { name: 'governance_review', sla: '24h', status: 'under_review' },
  4: { name: 'human_arbitration', sla: '72h', status: 'arbitration' },
  5: { name: 'constitutional_review', sla: '14d', status: 'constitutional_review' },
}

// POST / — report conflict
conflictRoutes.post('/', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')

  let body: CreateConflictBody
  try {
    body = createConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  // Map severity to start level: critical=3, high=2, else=1
  const startLevel = body.severity === 'critical' ? 3 : body.severity === 'high' ? 2 : 1
  const levelInfo = RESOLUTION_LEVELS[startLevel]!

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO conflicts (id, tenant_id, reporter_id, against_id, conflict_type, description, severity, resolution_level, status)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenant.id, body.reporter_id, body.against_id ?? null, body.conflict_type,
      body.description, body.severity, startLevel, 'open').run(),
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
  const tenant = c.get('tenant')
  const id = c.req.param('id')

  let body: EscalateConflictBody
  try {
    body = escalateConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const conflict = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        'SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?'
      ).bind(id, tenant.id).first()
      return result as { resolution_level: number; status: string } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch conflict'
  )
  if (!conflict) return c.json(createError('NOT_FOUND', 'Conflict not found'), 404)

  const currentLevel = conflict.resolution_level
  if (currentLevel >= 5) {
    return c.json(createError('BAD_REQUEST', 'Already at maximum resolution level (constitutional review)'), 400)
  }

  const resolvedStatuses = ['resolved', 'dismissed']
  if (resolvedStatuses.includes(conflict.status)) {
    return c.json(createError('BAD_REQUEST', 'Cannot escalate a resolved or dismissed conflict'), 400)
  }

  const newLevel = currentLevel + 1
  const levelInfo = RESOLUTION_LEVELS[newLevel]!

  // Update conflict level and status
  await handleDb(
    () => c.env.DB.prepare(
      'UPDATE conflicts SET resolution_level = ?, status = ? WHERE id = ?'
    ).bind(newLevel, levelInfo.status, id).run(),
    'DATABASE_ERROR',
    'Failed to update conflict'
  )

  // Log escalation
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO conflict_escalations (conflict_id, from_level, to_level, reason, escalated_by)
     VALUES (?, ?, ?, ?, ?)`
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
  const tenant = c.get('tenant')
  const id = c.req.param('id')

  let body: ResolveConflictBody
  try {
    body = resolveConflictSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const conflict = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        'SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?'
      ).bind(id, tenant.id).first()
      return result as { resolution_level: number; status: string } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch conflict'
  )
  if (!conflict) return c.json(createError('NOT_FOUND', 'Conflict not found'), 404)

  const finalStatus = body.dismissed ? 'dismissed' : 'resolved'
  const now = new Date().toISOString()

  await handleDb(
    () => c.env.DB.prepare(
      'UPDATE conflicts SET status = ?, resolution_notes = ?, resolved_at = ? WHERE id = ?'
    ).bind(finalStatus, body.resolution_notes ?? null, now, id).run(),
    'DATABASE_ERROR',
    'Failed to resolve conflict'
  )

  return c.json({ id, status: finalStatus, resolved_at: now })
}))

// GET / — list conflicts by status
conflictRoutes.get('/', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')
  const status = c.req.query('status')

  const query = status
    ? 'SELECT * FROM conflicts WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM conflicts WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rows = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(query).bind(...params).all()
      return result as { results?: { resolution_level: number }[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch conflicts'
  )

  // Enrich with resolution level info
  const conflicts = (rows.results || []).map((row) => ({
    ...row,
    resolution_info: RESOLUTION_LEVELS[row.resolution_level] ?? null,
  }))

  return c.json({ conflicts, total: conflicts.length })
}))

export { conflictRoutes }
