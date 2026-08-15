/**
 * chat.ts - Zalo OA + Facebook Messenger webhook routes
 * Receives messages -> KB lookup -> LLM reply -> send back to platform
 */
import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import { webhookRateLimit } from '../raas/rate-limit-middleware'
import { handleAsync, handleDb, createError } from '../types/error'
import { isDuplicateWebhookEvent, recordWebhookEvent } from '../lib/webhook-utils'
import { constantTimeCompare } from '../lib/crypto-utils'

// Zod schemas for webhook payloads
const zaloWebhookSchema = z.object({
  event_name: z.string(),
  app_id: z.string(),
  sender: z.object({ id: z.string() }),
  recipient: z.object({ id: z.string() }),
  message: z.object({ text: z.string(), msg_id: z.string() }).optional(),
  timestamp: z.string(),
})
type ZaloWebhookBody = z.infer<typeof zaloWebhookSchema>

const facebookMessageSchema = z.object({
  sender: z.object({ id: z.string() }),
  recipient: z.object({ id: z.string() }),
  message: z.object({ mid: z.string(), text: z.string() }).optional(),
  timestamp: z.number(),
})

const facebookEntrySchema = z.object({
  id: z.string(),
  messaging: z.array(facebookMessageSchema),
})

const facebookWebhookSchema = z.object({
  object: z.string(),
  entry: z.array(facebookEntrySchema),
})
type FacebookWebhookBody = z.infer<typeof facebookWebhookSchema>

const chatRoutes = new Hono<{ Bindings: Bindings }>()

// --- Zalo OA Webhook ---
chatRoutes.post('/webhook/zalo', webhookRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const db = c.env.DB

  const signature = c.req.header('x-zalo-signature') || c.req.header('x-signature')
  const secret = c.env.ZALO_APP_SECRET || c.env.ZALO_SECRET

  if (secret && signature) {
    const rawBody = await c.req.text()
    const expectedSig = await crypto.subtle.sign(
      'HMAC',
      await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(secret),
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      ),
      new TextEncoder().encode(rawBody)
    )
    const expectedHex = Array.from(new Uint8Array(expectedSig))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    if (!constantTimeCompare(signature, expectedHex)) {
      return c.json(createError('UNAUTHORIZED', 'Invalid Zalo signature'), 401)
    }
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

  // Check for replay attack (duplicate msg_id)
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

  // Record webhook event to prevent replay attacks
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

  // Verify Facebook signature
  const signature = c.req.header('X-Hub-Signature-256')?.replace('sha256=', '')
  const secret = c.env.FB_APP_SECRET

  if (secret && signature) {
    const rawBody = await c.req.text()
    const expectedSig = await crypto.subtle.sign(
      'HMAC',
      await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(secret),
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      ),
      new TextEncoder().encode(rawBody)
    )
    const expectedHex = Array.from(new Uint8Array(expectedSig))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    if (!constantTimeCompare(signature, expectedHex)) {
      return c.json(createError('UNAUTHORIZED', 'Invalid Facebook signature'), 401)
    }
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

      // Check for replay attack (duplicate mid)
      const mid = event.message.mid
      if (mid) {
        const isDuplicate = await isDuplicateWebhookEvent(db, 'facebook', mid)
        if (isDuplicate) {
          continue // Skip duplicate but continue processing other events
        }
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

      // Record webhook event to prevent replay attacks
      if (mid) {
        await recordWebhookEvent(db, 'facebook', mid, 'message')
      }
    }
  }
  return c.json({ received: true })
}))

// --- AI message processing: KB -> LLM -> reply -> save ---
async function processMessage(
  env: Bindings, tenantId: string, convId: string, userMessage: string,
  ctx: { platform: string; sender_id: string; access_token: string; [k: string]: string },
) {
  const db = env.DB!
  const kbMatch = await db.prepare(
    'SELECT answer FROM knowledge_base WHERE tenant_id = ? AND question LIKE ? LIMIT 1'
  ).bind(tenantId, `%${userMessage.replace(/[%_]/g, '\\$&').slice(0, 50)}%`).first()

  let reply: string
  if (kbMatch) {
    reply = kbMatch.answer as string
  } else {
    const history = await db.prepare(
      'SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 10'
    ).bind(convId).all()

    const messages = [
      { role: 'system' as const, content: 'Ban la tro ly AI cho doanh nghiep. Tra loi bang tieng Viet, ngan gon, than thien.' },
      ...(history.results || []).reverse().map((m: Record<string, unknown>) => ({
        role: m.role as 'user' | 'assistant', content: m.content as string,
      })),
      { role: 'user' as const, content: userMessage },
    ]

    const { LLMClient } = await import('../core/llm-client')
    const llm = new LLMClient({
      ai: env.AI, llmApiKey: env.LLM_API_KEY,
      llmBaseUrl: env.LLM_BASE_URL, model: env.DEFAULT_LLM_MODEL,
    })
    const response = await llm.chat(messages, { max_tokens: 300, temperature: 0.7 })
    reply = response.content
  }

  await db.prepare(
    'INSERT INTO messages (conversation_id, tenant_id, role, content) VALUES (?, ?, ?, ?)'
  ).bind(convId, tenantId, 'assistant', reply).run()

  if (ctx.platform === 'zalo') await sendZaloReply(ctx.access_token, ctx.sender_id, reply)
  else if (ctx.platform === 'facebook') await sendFBReply(ctx.access_token, ctx.sender_id, reply)
}

async function sendZaloReply(token: string, userId: string, text: string) {
  await fetch('https://openapi.zalo.me/v3.0/oa/message/cs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'access_token': token },
    body: JSON.stringify({ recipient: { user_id: userId }, message: { text } }),
  })
}

async function sendFBReply(token: string, recipientId: string, text: string) {
  await fetch(`https://graph.facebook.com/v19.0/me/messages?access_token=${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipient: { id: recipientId }, message: { text } }),
  })
}

export { chatRoutes }
