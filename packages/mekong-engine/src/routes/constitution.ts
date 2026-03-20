import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { enforceConstitution } from '../raas/constitution-enforcer'
import type { AgentAction } from '../raas/constitution-enforcer'
import { handleAsync, createError, validateJsonBody } from '../types/error'
import { z } from 'zod'

type Variables = { tenant: Tenant }
const constitutionRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
constitutionRoutes.use('*', authMiddleware)

// POST /v1/constitution/check — enforce 4-layer constitution against an agent action
constitutionRoutes.post('/check', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant') as Tenant

  const body = await validateJsonBody(c, z.object({
    agent_name: z.string().min(1, 'agent_name is required'),
    agent_layer: z.string().min(1, 'agent_layer is required'),
    action_type: z.string().min(1, 'action_type is required'),
    resource: z.string().min(1, 'resource is required'),
    estimated_cost_usd: z.number().optional(),
    target_stakeholder_id: z.string().optional(),
  }))

  const action: AgentAction = {
    ...body,
    tenant_id: tenant.id,
    agent_layer: body.agent_layer as AgentAction['agent_layer'],
    action_type: body.action_type as AgentAction['action_type'],
  }

  const result = await enforceConstitution(action, c.env.DB)
  return c.json(result, result.allowed ? 200 : 403)
}))

// GET /v1/constitution/layers — describe the 4 enforcement layers
constitutionRoutes.get('/layers', (c) => {
  return c.json({
    layers: [
      { id: 1, name: 'Firewall', desc: 'Bất khả xâm phạm — no override', rules: 5 },
      { id: 2, name: 'Balance', desc: 'Cân bằng đa bên — 75% supermajority to amend', rules: 5 },
      { id: 3, name: 'Agent Rules', desc: 'Per-layer autonomy — governance vote to adjust', rules: 6 },
      { id: 4, name: 'Terrain', desc: 'Cửu Địa adaptive — auto from Ngũ Sự scores', rules: 7 },
    ],
  })
})

export { constitutionRoutes }
