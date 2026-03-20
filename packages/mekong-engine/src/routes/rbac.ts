import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { checkPermission, getPolicies } from '../raas/rbac'
import { createError, handleAsync, handleDb } from '../types/error'
import { rateLimitMiddleware } from '../raas/rate-limit-middleware'

type Variables = { tenant: Tenant }

const checkPermissionSchema = z.object({
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  resource: z.string().min(1, 'resource is required'),
  action: z.string().min(1, 'action is required'),
})

type CheckPermissionBody = z.infer<typeof checkPermissionSchema>
const rbacRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
rbacRoutes.use('*', authMiddleware)

// GET /policies — list all RBAC policies (rate limited: 100 req/min)
rbacRoutes.get('/policies', rateLimitMiddleware('rbac_policies', 100, 60000), (c) => {
  return c.json({ policies: getPolicies(), total: getPolicies().length })
})

// POST /check — check permission for stakeholder
rbacRoutes.post('/check', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')

  let body: CheckPermissionBody
  try {
    body = checkPermissionSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const stakeholder = await handleDb(
    async () => {
      const result = await c.env.DB!.prepare(
        'SELECT id, role, governance_level FROM stakeholders WHERE id = ? AND tenant_id = ?'
      ).bind(body.stakeholder_id, tenant.id).first()
      return result as { id: string; role: string; governance_level: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch stakeholder'
  )

  if (!stakeholder) return c.json(createError('NOT_FOUND', 'Stakeholder not found'), 404)

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
}))

export { rbacRoutes }
