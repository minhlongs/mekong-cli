import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { checkPermission, getPolicies } from '../raas/rbac'

type Variables = { tenant: Tenant }
const rbacRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
rbacRoutes.use('*', authMiddleware)

// GET /policies — list all RBAC policies
rbacRoutes.get('/policies', (c) => {
  return c.json({ policies: getPolicies(), total: getPolicies().length })
})

// POST /check — check permission for stakeholder
rbacRoutes.post('/check', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: { stakeholder_id: string; resource: string; action: string }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }

  if (!body.stakeholder_id) return c.json({ error: 'stakeholder_id required' }, 400)
  if (!body.resource) return c.json({ error: 'resource required' }, 400)
  if (!body.action) return c.json({ error: 'action required' }, 400)

  const stakeholder = await c.env.DB.prepare(
    'SELECT id, role, governance_level FROM stakeholders WHERE id = ? AND tenant_id = ?'
  ).bind(body.stakeholder_id, tenant.id).first<{ id: string; role: string; governance_level: number }>()

  if (!stakeholder) return c.json({ error: 'Stakeholder not found' }, 404)

  const result = checkPermission(body.resource, body.action, stakeholder)

  return c.json({
    stakeholder_id: body.stakeholder_id,
    role: stakeholder.role,
    governance_level: stakeholder.governance_level,
    resource: body.resource,
    action: body.action,
    allowed: result.allowed,
    reason: result.reason,
    policy: result.policy ?? null,
  })
})

export { rbacRoutes }
