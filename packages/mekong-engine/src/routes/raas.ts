import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync } from '../types/error'
import { z } from 'zod'
import * as dunning from '../raas/dunning'
import { verifyPolarSignature } from '../raas/webhook-utils'

type Variables = { tenant: Tenant }
const raasRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
raasRoutes.use('*', authMiddleware)

// Public webhook routes (no auth required - signature verified)
const webhookRoutes = new Hono<{ Bindings: Bindings }>()

// POST /webhooks/polar - Handle Polar.sh webhook events
webhookRoutes.post('/polar', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json()
  const signature = c.req.header('X-Polar-Signature')
  const secret = c.env.POLAR_WEBHOOK_SECRET

  // Verify webhook signature
  const isValid = await verifyPolarSignature(body, signature, secret)
  if (!isValid) {
    return c.json({ error: 'Invalid signature' }, 401)
  }

  // Route to appropriate handler based on event type
  const eventType = body.type as string
  const data = body.data || {}

  switch (eventType) {
    case 'payment.succeeded':
      await dunning.handlePaymentSucceeded(c.env.DB, data)
      break
    case 'payment.failed':
      await dunning.handlePaymentFailed(c.env.DB, data)
      break
    case 'subscription.active':
      await dunning.handleSubscriptionActive(c.env.DB, data)
      break
    case 'subscription.expired':
      await dunning.handleSubscriptionExpired(c.env.DB, data)
      break
    case 'subscription.canceled':
      await dunning.handleSubscriptionCanceled(c.env.DB, data)
      break
    default:
      // Unknown event type - just acknowledge
      break
  }

  return c.json({ success: true, event: eventType })
}))

// Validation schemas
const suspendSchema = z.object({
  tenant_id: z.string().uuid(),
  reason: z.string().min(1),
})

const reactivateSchema = z.object({
  tenant_id: z.string().uuid(),
  new_tier: z.enum(['free', 'pro', 'enterprise']).optional().default('free'),
})

// POST /v1/raas/suspend - Suspend tenant access
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

// POST /v1/raas/reactivate - Reactivate suspended tenant
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

// GET /v1/raas/license/status - Check current tenant's license status
raasRoutes.get('/license/status', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const status = await dunning.checkLicenseStatus(c.env.DB, tenant.id)
  const schedule = await dunning.getDunningSchedule(c.env.DB, tenant.id)

  return c.json({
    tenant_id: tenant.id,
    status,
    tier: tenant.tier,
    days_until_suspension: schedule.daysUntilSuspension,
    grace_period_ends: schedule.gracePeriodEnds,
  })
}))

// GET /v1/raas/dunning/schedule - Get detailed dunning schedule
raasRoutes.get('/dunning/schedule', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const schedule = await dunning.getDunningSchedule(c.env.DB, tenant.id)

  return c.json({
    tenant_id: tenant.id,
    ...schedule,
  })
}))

export { raasRoutes, webhookRoutes }
