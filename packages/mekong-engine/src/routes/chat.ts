/**
 * chat.ts - Zalo OA + Facebook Messenger webhook routes
 * Receives messages -> KB lookup -> LLM reply -> send back to platform
 */
import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import { webhookRateLimit } from '../raas/rate-limit-middleware'
import { handleAsync, createError } from '../types/error'
import { isDuplicateWebhookEvent, recordWebhookEvent } from '../lib/webhook-utils'
import {
  zaloWebhookSchema,
  type ZaloWebhookBody,
  facebookWebhookSchema,
  type FacebookWebhookBody,
  verifyHmacSha256Signature,
  processMessage,
} from './chat-processor'

const chatRoutes = new Hono<{ Bindings: Bindings }>()

// --- Zalo OA Webhook ---
chatRoutes.post('/webhook/zalo', webhookRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const db = c.env.DB

  const signature = c.req.header('x-zalo-signature') || c.req.header('x-signature')
  const secret = c.env.ZALO_APP_SECRET || c.env.ZALO_SECRET

  if (!secret) {
    return c.json(createError('SERVICE_UNAVAILABLE', 'Webhook authentication is not configured'), 503)
  }
  if (!signature) {
    return c.json(createError('UNAUTHORIZED', 'Missing Zalo signature'), 401)
  }
  const rawBody = await c.req.text()
  const valid = await verifyHmacSha256Signature(secret, rawBody, signature)
  if (!valid) {
    return c.json(createError('UNAUTHORIZED', 'Invalid Zalo signature'), 401)
  }

  let body: ZaloWebhookBody
  try {
    body = zaloWebhookSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid Zalo webhook payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  if (body.event_name !== 'user_send_text' || !body.message?.text) {
    return c.json({ received: true })
  }

  const msgId = body.message.msg_id
  if (msgId) {
    const isDuplicate = await isDuplicateWebhookEvent(db, 'zalo', msgId)
    if (isDuplicate) {
      return c.json(createError('REPLAY_ATTACK', 'Duplicate Zalo message detected'), 409)
    }
  }

  const channel = await c.env.DB!.prepare(
    'SELECT ch.*, ch.tenant_id FROM channels ch WHERE ch.type = ? AND ch.external_id = ? AND ch.active = 1'
  ).bind('zalo_oa', body.recipient.id).first()

  if (!channel) return c.json({ received: true })

  const convId = `zalo_${body.recipient.id}_${body.sender.id}`
  await c.env.DB!.prepare(`
    INSERT INTO conversations (id, tenant_id, channel_id, external_user_id, last_message_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    ON CONFLICT(id) DO UPDATE SET last_message_at = datetime('now'), status = 'active'
  `).bind(convId, channel.tenant_id, channel.id, body.sender.id).run()

  await c.env.DB!.prepare(
    'INSERT INTO messages (conversation_id, tenant_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)'
  ).bind(convId, channel.tenant_id, 'user', body.message.text, JSON.stringify({
    msg_id: body.message.msg_id, platform: 'zalo', sender_id: body.sender.id
  })).run()

  c.executionCtx.waitUntil(processMessage(c.env, channel.tenant_id as string, convId, body.message.text, {
    platform: 'zalo', sender_id: body.sender.id,
    oa_id: body.recipient.id, access_token: channel.access_token_encrypted as string,
  }))

  if (msgId) {
    await recordWebhookEvent(db, 'zalo', msgId, 'message')
  }

  return c.json({ received: true })
}))

// --- Facebook Messenger Webhook ---
chatRoutes.get('/webhook/facebook', (c) => {
  const mode = c.req.query('hub.mode')
  const token = c.req.query('hub.verify_token')
  const challenge = c.req.query('hub.challenge')
  const verifyToken = c.env.FB_VERIFY_TOKEN
  if (!verifyToken) {
    return c.text('Forbidden', 403)
  }
  if (mode === 'subscribe' && token === verifyToken) return c.text(challenge || '', 200)
  return c.text('Forbidden', 403)
})

chatRoutes.post('/webhook/facebook', webhookRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const db = c.env.DB

  const signature = c.req.header('X-Hub-Signature-256')?.replace('sha256=', '')
  const secret = c.env.FB_APP_SECRET

  if (!secret) {
    return c.json(createError('SERVICE_UNAVAILABLE', 'Webhook authentication is not configured'), 503)
  }
  if (!signature) {
    return c.json(createError('UNAUTHORIZED', 'Missing Facebook signature'), 401)
  }
  const rawBody = await c.req.text()
  const valid = await verifyHmacSha256Signature(secret, rawBody, signature)
  if (!valid) {
    return c.json(createError('UNAUTHORIZED', 'Invalid Facebook signature'), 401)
  }

  let body: FacebookWebhookBody
  try {
    body = facebookWebhookSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid Facebook webhook payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  if (!c.env.DB || body.object !== 'page') return c.json({ received: true })

  for (const entry of body.entry) {
    for (const event of entry.messaging) {
      if (!event.message?.text) continue

      const mid = event.message.mid
      if (mid && (await isDuplicateWebhookEvent(db, 'facebook', mid))) {
        continue
      }

      const channel = await c.env.DB!.prepare(
        'SELECT * FROM channels WHERE type = ? AND external_id = ? AND active = 1'
      ).bind('facebook', entry.id).first()
      if (!channel) continue

      const convId = `fb_${entry.id}_${event.sender.id}`
      await c.env.DB!.prepare(`
        INSERT INTO conversations (id, tenant_id, channel_id, external_user_id, last_message_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET last_message_at = datetime('now')
      `).bind(convId, channel.tenant_id, channel.id, event.sender.id).run()

      await c.env.DB!.prepare(
        'INSERT INTO messages (conversation_id, tenant_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)'
      ).bind(convId, channel.tenant_id, 'user', event.message.text, JSON.stringify({
        mid: event.message.mid, platform: 'facebook'
      })).run()

      c.executionCtx.waitUntil(processMessage(c.env, channel.tenant_id as string, convId, event.message.text, {
        platform: 'facebook', sender_id: event.sender.id,
        page_id: entry.id, access_token: channel.access_token_encrypted as string,
      }))

      if (mid) {
        await recordWebhookEvent(db, 'facebook', mid, 'message')
      }
    }
  }
  return c.json({ received: true })
}))

export { chatRoutes }
