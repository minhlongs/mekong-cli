import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { enforceConstitution } from '../raas/constitution-enforcer'
import type { AgentAction } from '../raas/constitution-enforcer'

type Variables = { tenant: Tenant }
const constitutionRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
constitutionRoutes.use('*', authMiddleware)

// POST /v1/constitution/check — enforce 4-layer constitution against an agent action
constitutionRoutes.post('/check', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: {
    agent_name: string
    agent_layer: string
    action_type: string
    resource: string
    estimated_cost_usd?: number
    target_stakeholder_id?: string
  }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  if (!body.agent_name || !body.agent_layer || !body.action_type || !body.resource) {
    return c.json({ error: 'agent_name, agent_layer, action_type, resource are required' }, 400)
  }

  const action: AgentAction = {
    ...body,
    tenant_id: tenant.id,
    agent_layer: body.agent_layer as AgentAction['agent_layer'],
    action_type: body.action_type as AgentAction['action_type'],
  }

  const result = await enforceConstitution(action, c.env.DB)
  return c.json(result, result.allowed ? 200 : 403)
})

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
