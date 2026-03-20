import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import type { Variables } from '../raas/auth-middleware'
import { authMiddleware } from '../raas/auth-middleware'
import { getBalance, getHistory, addCredits } from '../raas/credits'
import { createTenant, regenerateApiKey } from '../raas/tenant'
import { z } from 'zod'
import { handleAsync, handleDb, createError } from '../types/error'
import { authRateLimit, webhookRateLimit } from '../raas/rate-limit-middleware'
import { ensureWebhookEventsTable, isDuplicateWebhookEvent, recordWebhookEvent } from '../lib/webhook-utils'
import {
  checkLicenseStatus,
  suspendTenant,
  reactivateTenant,
  getDunningSchedule,
  emitLicenseEvent,
} from '../raas/dunning'
import { requireActiveLicense } from '../raas/license-middleware'
import { constantTimeCompare } from '../lib/crypto-utils'

const billingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

// Zod schemas for validation
const createTenantSchema = z.object({
  name: z.string().min(1, 'Tenant name is required').trim(),
})

const regenerateKeySchema = z.object({
  tenant_id: z.string().min(1, 'Tenant ID is required').trim(),
  name: z.string().min(1, 'Tenant name is required').trim(),
})

// Create tenant - returns API key (one-time display)
billingRoutes.post('/tenants', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const parsed = createTenantSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)
  const { tenant, apiKey } = await createTenant(c.env.DB, parsed.data.name)
  // Grant 10 free welcome credits so user can start immediately
  await addCredits(c.env.DB, tenant.id, 10, 'welcome: free tier bonus')
  return c.json({
    tenant_id: tenant.id, name: tenant.name, api_key: apiKey, tier: tenant.tier,
    credits: 10, message: 'Save your API key - it cannot be recovered if lost!',
  }, 201)
}))

// Regenerate API key - requires tenant_id + name as ownership proof
billingRoutes.post('/tenants/regenerate-key', authRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const parsed = regenerateKeySchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)
  const result = await regenerateApiKey(c.env.DB, parsed.data.tenant_id, parsed.data.name)
  if (!result) return c.json({ error: 'Tenant not found or name mismatch' }, 404)
  return c.json({
    api_key: result.apiKey,
    message: 'New API key generated. Old key is now invalid. Save this key!',
  })
}))

// Polar product -> credit mapping (match Polar.sh product names)
const POLAR_PRODUCT_CREDITS: Record<string, number> = {
  'agencyos-starter': 50,
  'agencyos-pro': 200,
  'agencyos-agency': 500,
  'agencyos-master': 1000,
  'credits-10': 10,
  'credits-50': 50,
  'credits-100': 100,
}

// Polar tier -> tenant tier mapping
const POLAR_TIER_MAP: Record<string, string> = {
  'agencyos-starter': 'pro',
  'agencyos-pro': 'pro',
  'agencyos-agency': 'enterprise',
  'agencyos-master': 'enterprise',
}

billingRoutes.post('/webhook', webhookRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
  const db = c.env.DB
  await ensureWebhookEventsTable(db)
  const secret = c.env.POLAR_WEBHOOK_SECRET ?? ''
  const signature = c.req.header('webhook-signature') ?? ''
  const rawBody = await c.req.text()

  // Verify webhook signature if secret configured
  if (secret && signature) {
    const keyData = new TextEncoder().encode(secret)
    const msgData = new TextEncoder().encode(rawBody)
    const cryptoKey = await crypto.subtle.importKey(
      'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
    )
    const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData)
    const expectedSig = Array.from(new Uint8Array(sigBuffer))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    if (!constantTimeCompare(signature, expectedSig)) {
      return c.json({ error: 'Invalid webhook signature' }, 401)
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let event: { type: string; data?: unknown; timestamp?: string; created_at?: string; id?: string }
  try {
    event = JSON.parse(rawBody)
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  // Check for replay attack (duplicate event ID)
  if (event.id) {
    const eventId: string = event.id // Type guard: narrow from string | undefined
    const isDuplicate = await handleDb(
      () => isDuplicateWebhookEvent(db, 'polar', eventId),
      'DATABASE_ERROR',
      'Failed to check for duplicate webhook event'
    ) as boolean
    if (isDuplicate) {
      return c.json({ error: 'Duplicate event detected', code: 'REPLAY_ATTACK' }, 409)
    }
  }

  // Add timestamp validation to prevent replay attacks (5 minute window)
  const timestamp = event.timestamp ?? event.created_at
  if (timestamp) {
    const eventTime = new Date(timestamp).getTime()
    const now = Date.now()
    const age = now - eventTime
    if (age > 5 * 60 * 1000) { // 5 minutes
      return c.json({ error: 'Webhook timestamp too old (replay attack prevented)', code: 'REPLAY_ATTACK' }, 401)
    }
    if (age < 0) {
      return c.json({ error: 'Webhook timestamp in future', code: 'INVALID_TIMESTAMP' }, 400)
    }
  }

  const data = event.data ?? {} as Record<string, any>

  if (event.type === 'order.paid') {
    // Support both: direct tenant_id/credits OR Polar product mapping
    const typedData = data as { tenant_id?: string; metadata?: { tenant_id?: string }; customer?: { external_id?: string }; product_name?: string; product?: { name?: string }; credits?: number }
    const tenantId: string | undefined =
      typedData.tenant_id ?? typedData.metadata?.tenant_id ?? typedData.customer?.external_id
    if (!tenantId) return c.json({ error: 'No tenant_id in webhook payload' }, 400)

    const productName: string = typedData.product_name ?? typedData.product?.name ?? ''
    const productKey = productName.toLowerCase().replace(/\s+/g, '-')
    const mappedCredits = POLAR_PRODUCT_CREDITS[productKey]
    const credits: number = mappedCredits ?? typedData.credits ?? 0

    if (credits > 0) {
      const reason = mappedCredits
        ? `Polar.sh: ${productName} (${credits} credits)`
        : `Polar.sh purchase: ${credits} credits`
      await addCredits(db, tenantId, credits, reason)
    }

    // Upgrade tenant tier if subscription product
    const newTier = POLAR_TIER_MAP[productKey]
    if (newTier) {
      await db.prepare('UPDATE tenants SET tier = ? WHERE id = ?').bind(newTier, tenantId).run()
    }
  }

  if (event.type === 'subscription.canceled') {
    const typedData = data as { customer?: { external_id?: string }; tenant_id?: string }
    const tenantId: string | undefined = typedData.customer?.external_id ?? typedData.tenant_id
    if (tenantId) {
      await db.prepare('UPDATE tenants SET tier = ? WHERE id = ?').bind('free', tenantId).run()
    }
  }

  // Record webhook event to prevent replay attacks
  if (event.id) {
    const eventId: string = event.id // Type guard: narrow from string | undefined
    await handleDb(
      () => recordWebhookEvent(db, 'polar', eventId, event.type),
      'DATABASE_ERROR',
      'Failed to record Polar webhook event'
    ) as void
  }

  return c.json({ received: true })
}))

// Public pricing info - landing page + dashboard can fetch this
billingRoutes.get('/pricing', handleAsync(async (c) => {
  return c.json({
    tiers: [
      { id: 'free', name: 'Free', price: 0, credits: 10, description: 'Try it out' },
      { id: 'agencyos-starter', name: 'Starter', price: 29, credits: 50, description: 'Solo non-tech user' },
      { id: 'agencyos-pro', name: 'Pro', price: 99, credits: 200, description: 'Small agency' },
      { id: 'agencyos-agency', name: 'Agency', price: 199, credits: 500, description: 'Growing agency' },
      { id: 'agencyos-master', name: 'Master', price: 399, credits: 1000, description: 'Premium agency' },
    ],
    credit_packs: [
      { id: 'credits-10', credits: 10, price: 5 },
      { id: 'credits-50', credits: 50, price: 20 },
      { id: 'credits-100', credits: 100, price: 35 },
    ],
    credit_costs: { simple: 1, standard: 3, complex: 5 },
  })
}))

billingRoutes.get('/credits', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const balance = await getBalance(c.env.DB, tenant.id)
  return c.json({ tenant_id: tenant.id, balance, tier: tenant.tier })
}))

billingRoutes.get('/credits/history', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '50', 10) || 50, 1), 200)
  const history = await getHistory(c.env.DB, tenant.id, limit)
  return c.json({ tenant_id: tenant.id, history, limit })
}))

// Dunning System Endpoints

// Check license status
billingRoutes.get('/license/status', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const status = await checkLicenseStatus(c.env.DB, tenant.id)
  const schedule = await getDunningSchedule(c.env.DB, tenant.id)
  return c.json({ tenant_id: tenant.id, status, schedule })
}))

// Suspend tenant (admin action)
billingRoutes.post('/license/suspend', authMiddleware, requireActiveLicense, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const body = await c.req.json().catch(() => ({}))
  const reason = body.reason || 'Suspended by admin'

  const success = await suspendTenant(c.env.DB, tenant.id, reason)
  if (!success) {
    return c.json({ error: 'Failed to suspend tenant' }, 500)
  }

  await emitLicenseEvent(c.env.DB, tenant.id, 'license.suspended', { reason })
  return c.json({ tenant_id: tenant.id, status: 'suspended', reason })
}))

// Reactivate tenant (admin action)
billingRoutes.post('/license/reactivate', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const body = await c.req.json().catch(() => ({}))
  const tier = body.tier || 'free'

  const success = await reactivateTenant(c.env.DB, tenant.id, tier)
  if (!success) {
    return c.json({ error: 'Failed to reactivate tenant' }, 500)
  }

  await emitLicenseEvent(c.env.DB, tenant.id, 'license.reactivated', { tier })
  return c.json({ tenant_id: tenant.id, status: 'active', tier })
}))

// Get dunning schedule
billingRoutes.get('/dunning/schedule', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const schedule = await getDunningSchedule(c.env.DB, tenant.id)
  return c.json({ tenant_id: tenant.id, schedule })
}))

export { billingRoutes }
