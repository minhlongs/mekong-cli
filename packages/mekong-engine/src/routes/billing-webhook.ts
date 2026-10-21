import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Variables } from '../raas/auth-middleware'
import { addCredits } from '../raas/credits'
import { handleAsync, handleDb } from '../types/error'
import { webhookRateLimit } from '../raas/rate-limit-middleware'
import { ensureWebhookEventsTable, isDuplicateWebhookEvent, recordWebhookEvent } from '../lib/webhook-utils'
import { constantTimeCompare } from '../lib/crypto-utils'

const NOWPAYMENTS_PRODUCT_CREDITS: Record<string, number> = {
  'agencyos-starter': 50,
  'agencyos-pro': 200,
  'agencyos-agency': 500,
  'agencyos-master': 1000,
  'credits-10': 10,
  'credits-50': 50,
  'credits-100': 100,
  'credits-500': 500,
}

const NOWPAYMENTS_TIER_MAP: Record<string, string> = {
  'agencyos-starter': 'pro',
  'agencyos-pro': 'pro',
  'agencyos-agency': 'enterprise',
  'agencyos-master': 'enterprise',
}

interface NowPaymentsOrderPayload {
  tenant_id?: string
  metadata?: { tenant_id?: string }
  customer?: { external_id?: string }
  product_name?: string
  product?: { name?: string }
  credits?: number
}

export function registerBillingWebhookRoutes(billingRoutes: Hono<{ Bindings: Bindings; Variables: Variables }>): void {
  billingRoutes.post('/webhook', webhookRateLimit(), handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)
    const db = c.env.DB
    await ensureWebhookEventsTable(db)
    const secret = c.env.NOWPAYMENTS_WEBHOOK_SECRET ?? ''
    const signature = c.req.header('webhook-signature') ?? ''
    const rawBody = await c.req.text()

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

      if (!constantTimeCompare(signature, expectedSig)) {
        return c.json({ error: 'Invalid webhook signature' }, 401)
      }
    }

    let event: { type: string; data?: NowPaymentsOrderPayload; timestamp?: string; created_at?: string; id?: string }
    try {
      event = JSON.parse(rawBody)
    } catch {
      return c.json({ error: 'Invalid JSON' }, 400)
    }

    if (event.id) {
      const eventId: string = event.id
      const isDuplicate = await handleDb(
        () => isDuplicateWebhookEvent(db, 'nowpayments', eventId),
        'DATABASE_ERROR',
        'Failed to check for duplicate webhook event',
      ) as boolean
      if (isDuplicate) {
        return c.json({ error: 'Duplicate event detected', code: 'REPLAY_ATTACK' }, 409)
      }
    }

    const timestamp = event.timestamp ?? event.created_at
    if (timestamp) {
      const eventTime = new Date(timestamp).getTime()
      const age = Date.now() - eventTime
      if (age > 5 * 60 * 1000) {
        return c.json({ error: 'Webhook timestamp too old (replay attack prevented)', code: 'REPLAY_ATTACK' }, 401)
      }
      if (age < 0) {
        return c.json({ error: 'Webhook timestamp in future', code: 'INVALID_TIMESTAMP' }, 400)
      }
    }

    const typedData: NowPaymentsOrderPayload = event.data ?? {}

    if (event.type === 'order.paid') {
      const tenantId = typedData.tenant_id ?? typedData.metadata?.tenant_id ?? typedData.customer?.external_id
      if (!tenantId) return c.json({ error: 'No tenant_id in webhook payload' }, 400)

      const productName = typedData.product_name ?? typedData.product?.name ?? ''
      const productKey = productName.toLowerCase().replace(/\s+/g, '-')
      const mappedCredits = NOWPAYMENTS_PRODUCT_CREDITS[productKey]
      const credits = mappedCredits ?? typedData.credits ?? 0

      if (credits > 0) {
        const reason = mappedCredits
          ? `NOWPayments: ${productName} (${credits} credits)`
          : `NOWPayments purchase: ${credits} credits`
        await addCredits(db, tenantId, credits, reason)
      }

      const newTier = NOWPAYMENTS_TIER_MAP[productKey]
      if (newTier) {
        await db.prepare('UPDATE tenants SET tier = ? WHERE id = ?').bind(newTier, tenantId).run()
      }
    }

    if (event.type === 'subscription.canceled') {
      const tenantId = typedData.customer?.external_id ?? typedData.tenant_id
      if (tenantId) {
        await db.prepare('UPDATE tenants SET tier = ? WHERE id = ?').bind('free', tenantId).run()
      }
    }

    if (event.id) {
      const eventId: string = event.id
      await handleDb(
        () => recordWebhookEvent(db, 'nowpayments', eventId, event.type),
        'DATABASE_ERROR',
        'Failed to record NOWPayments webhook event',
      )
    }

    return c.json({ received: true })
  }))
}
