import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync } from '../types/error'
import { z } from 'zod'
import * as dunning from '../raas/dunning'
import { webhookRoutes } from './raas-webhooks'

type Variables = { tenant: Tenant }
const raasRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
raasRoutes.use('*', authMiddleware)

const suspendSchema = z.object({
  tenant_id: z.string().uuid(),
  reason: z.string().min(1),
})

const reactivateSchema = z.object({
  tenant_id: z.string().uuid(),
  new_tier: z.enum(['free', 'pro', 'enterprise']).optional().default('free'),
})

raasRoutes.post('/suspend', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  let body: unknown
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  const parsed = suspendSchema.safeParse(body)
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.errors }, 400)
  }

  const { tenant_id, reason } = parsed.data
  const success = await dunning.suspendTenant(c.env.DB, tenant_id, reason)
  if (!success) {
    return c.json({ error: 'Failed to suspend tenant' }, 500)
  }

  await dunning.emitLicenseEvent(c.env.DB, tenant_id, 'license.suspended', { reason })
  return c.json({
    success: true,
    tenant_id,
    status: 'suspended',
    suspended_at: new Date().toISOString(),
  })
}))

raasRoutes.post('/reactivate', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  let body: unknown
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  const parsed = reactivateSchema.safeParse(body)
  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.errors }, 400)
  }

  const { tenant_id, new_tier } = parsed.data
  const success = await dunning.reactivateTenant(c.env.DB, tenant_id, new_tier)
  if (!success) {
    return c.json({ error: 'Failed to reactivate tenant' }, 500)
  }

  await dunning.emitLicenseEvent(c.env.DB, tenant_id, 'license.reactivated', {
    trigger: 'manual',
    tier: new_tier,
  })

  return c.json({
    success: true,
    tenant_id,
    status: 'active',
    tier: new_tier,
    reactivated_at: new Date().toISOString(),
  })
}))

raasRoutes.get('/license/status', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const status = await dunning.checkLicenseStatus(c.env.DB, tenant.id)
  const schedule = await dunning.getDunningSchedule(c.env.DB, tenant.id)

  return c.json({
    tenant_id: (tenant as { id: string }).id,
    status,
    tier: (tenant as { tier: string }).tier,
    days_until_suspension: schedule.daysUntilSuspension,
    grace_period_ends: schedule.gracePeriodEnds,
  })
}))

raasRoutes.get('/dunning/schedule', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const schedule = await dunning.getDunningSchedule(c.env.DB, tenant.id)
  return c.json({
    tenant_id: (tenant as { id: string }).id,
    ...schedule,
  })
}))

export { raasRoutes, webhookRoutes }
