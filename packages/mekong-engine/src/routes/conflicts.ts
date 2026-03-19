import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'

type Variables = { tenant: Tenant }
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
conflictRoutes.post('/', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: {
    reporter_id: string
    against_id?: string
    conflict_type: string
    description: string
    severity?: string
  }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  if (!body.reporter_id) return c.json({ error: 'reporter_id required' }, 400)
  if (!body.conflict_type) return c.json({ error: 'conflict_type required' }, 400)
  if (!body.description) return c.json({ error: 'description required' }, 400)

  const validTypes = ['resource', 'equity', 'decision', 'conduct', 'constitutional']
  if (!validTypes.includes(body.conflict_type)) {
    return c.json({ error: `conflict_type must be one of: ${validTypes.join(', ')}` }, 400)
  }

  const severity = body.severity || 'medium'
  const validSeverities = ['low', 'medium', 'high', 'critical']
  if (!validSeverities.includes(severity)) {
    return c.json({ error: `severity must be one of: ${validSeverities.join(', ')}` }, 400)
  }

  // Map severity to start level: critical=3, high=2, else=1
  const startLevel = severity === 'critical' ? 3 : severity === 'high' ? 2 : 1
  const levelInfo = RESOLUTION_LEVELS[startLevel]!

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO conflicts (id, tenant_id, reporter_id, against_id, conflict_type, description, severity, resolution_level, status)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenant.id, body.reporter_id, body.against_id ?? null, body.conflict_type,
    body.description, severity, startLevel, 'open').run()

  return c.json({
    id,
    severity,
    resolution_level: startLevel,
    resolution_name: levelInfo.name,
    sla: levelInfo.sla,
    status: 'open',
    message: `Conflict reported. Resolution: ${levelInfo.name} (SLA: ${levelInfo.sla})`,
  }, 201)
})

// POST /:id/escalate — increase resolution level
conflictRoutes.post('/:id/escalate', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const id = c.req.param('id')

  let body: { reason: string; escalated_by?: string }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  if (!body.reason) return c.json({ error: 'reason required' }, 400)

  const conflict = await c.env.DB.prepare(
    'SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenant.id).first()
  if (!conflict) return c.json({ error: 'Conflict not found' }, 404)

  const currentLevel = conflict.resolution_level as number
  if (currentLevel >= 5) {
    return c.json({ error: 'Already at maximum resolution level (constitutional review)' }, 400)
  }

  const resolvedStatuses = ['resolved', 'dismissed']
  if (resolvedStatuses.includes(conflict.status as string)) {
    return c.json({ error: 'Cannot escalate a resolved or dismissed conflict' }, 400)
  }

  const newLevel = currentLevel + 1
  const levelInfo = RESOLUTION_LEVELS[newLevel]!

  // Update conflict level and status
  await c.env.DB.prepare(
    'UPDATE conflicts SET resolution_level = ?, status = ? WHERE id = ?'
  ).bind(newLevel, levelInfo.status, id).run()

  // Log escalation
  await c.env.DB.prepare(
    `INSERT INTO conflict_escalations (conflict_id, from_level, to_level, reason, escalated_by)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(id, currentLevel, newLevel, body.reason, body.escalated_by ?? null).run()

  return c.json({
    id,
    from_level: currentLevel,
    to_level: newLevel,
    resolution_name: levelInfo.name,
    sla: levelInfo.sla,
    status: levelInfo.status,
    message: `Escalated to level ${newLevel}: ${levelInfo.name} (SLA: ${levelInfo.sla})`,
  })
})

// POST /:id/resolve — close with notes
conflictRoutes.post('/:id/resolve', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const id = c.req.param('id')

  let body: { resolution_notes?: string; dismissed?: boolean }
  try {
    body = await c.req.json()
  } catch {
    body = {}
  }

  const conflict = await c.env.DB.prepare(
    'SELECT * FROM conflicts WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenant.id).first()
  if (!conflict) return c.json({ error: 'Conflict not found' }, 404)

  const finalStatus = body.dismissed ? 'dismissed' : 'resolved'
  const now = new Date().toISOString()

  await c.env.DB.prepare(
    'UPDATE conflicts SET status = ?, resolution_notes = ?, resolved_at = ? WHERE id = ?'
  ).bind(finalStatus, body.resolution_notes ?? null, now, id).run()

  return c.json({ id, status: finalStatus, resolved_at: now })
})

// GET / — list conflicts by status
conflictRoutes.get('/', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const status = c.req.query('status')

  const query = status
    ? 'SELECT * FROM conflicts WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 50'
    : 'SELECT * FROM conflicts WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50'
  const params = status ? [tenant.id, status] : [tenant.id]
  const rows = await c.env.DB.prepare(query).bind(...params).all()

  // Enrich with resolution level info
  const conflicts = (rows.results || []).map((row) => ({
    ...row,
    resolution_info: RESOLUTION_LEVELS[row.resolution_level as number] ?? null,
  }))

  return c.json({ conflicts, total: conflicts.length })
})

export { conflictRoutes }
