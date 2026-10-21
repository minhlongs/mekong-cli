import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Variables } from '../raas/auth-middleware'
import { handleAsync } from '../types/error'
import * as dunning from '../raas/dunning'
import { verifyNowPaymentsSignature } from '../raas/webhook-utils'
import {
  handleSubscriptionCancelled,
  handleSubscriptionCreated,
  verifyPolarSignature,
  type PolarWebhookEvent,
} from '../raas/polar-webhook'
import { isPilotModeEnabled } from '../raas/invite-codes'
import { webhookSecurityHeaders } from '../middleware/security'

const webhookRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
webhookRoutes.use('*', webhookSecurityHeaders())

const handleNowPaymentsWebhook = handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = (await c.req.json()) as { type?: string; data?: Record<string, unknown> }
  const signature = c.req.header('X-NOWPayments-Signature')
  const secret = c.env.NOWPAYMENTS_WEBHOOK_SECRET

  const isValid = await verifyNowPaymentsSignature(body, signature, secret)
  if (!isValid) {
    return c.json({ error: 'Invalid signature' }, 401)
  }

  const eventType = String(body.type ?? '')
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
      break
  }

  return c.json({ success: true, event: eventType })
})

const handlePolarWebhook = handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const raw = await c.req.text()
  const webhookId = c.req.header('webhook-id')
  const webhookTimestamp = c.req.header('webhook-timestamp')
  const signature = c.req.header('webhook-signature')
  const valid = await verifyPolarSignature(raw, webhookId, webhookTimestamp, signature, c.env.POLAR_WEBHOOK_SECRET)
  if (!valid) {
    return c.json({ error: 'Invalid signature' }, 401)
  }

  let body: PolarWebhookEvent
  try {
    body = JSON.parse(raw) as PolarWebhookEvent
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  const eventType: string = body?.type ?? body?.event ?? ''
  switch (eventType) {
    case 'subscription.created':
    case 'subscription.active': {
      const pilotMode = isPilotModeEnabled(c.env.PILOT_MODE)
      const result = await handleSubscriptionCreated(c.env.DB, body, { pilotMode })
      if (!result) {
        return c.json({
          status: 'skipped',
          reason: pilotMode ? 'pilot_invite_required_or_missing_customer' : 'missing_customer',
        })
      }
      return c.json({
        status: 'ok',
        tenant_id: result.tenantId,
        tier: result.tier,
        credits_granted: result.creditsGranted,
        license_key_preview: `${result.licenseKey.slice(0, 12)}...`,
      })
    }
    case 'subscription.cancelled':
    case 'subscription.canceled':
    case 'subscription.revoked': {
      const ok = await handleSubscriptionCancelled(c.env.DB, body)
      return c.json({ status: ok ? 'cancelled' : 'noop' })
    }
    default:
      return c.json({ status: 'ignored', type: eventType })
  }
})

webhookRoutes.post('/nowpayments', handleNowPaymentsWebhook)
webhookRoutes.post('/webhooks/nowpayments', handleNowPaymentsWebhook)
webhookRoutes.post('/polar', handlePolarWebhook)
webhookRoutes.post('/webhooks/polar', handlePolarWebhook)

export { webhookRoutes }
