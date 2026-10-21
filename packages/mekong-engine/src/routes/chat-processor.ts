import { z } from 'zod'
import type { Bindings } from '../index'
import { constantTimeCompare } from '../lib/crypto-utils'

export const zaloWebhookSchema = z.object({
  event_name: z.string(),
  app_id: z.string(),
  sender: z.object({ id: z.string() }),
  recipient: z.object({ id: z.string() }),
  message: z.object({ text: z.string(), msg_id: z.string() }).optional(),
  timestamp: z.string(),
})
export type ZaloWebhookBody = z.infer<typeof zaloWebhookSchema>

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

export const facebookWebhookSchema = z.object({
  object: z.string(),
  entry: z.array(facebookEntrySchema),
})
export type FacebookWebhookBody = z.infer<typeof facebookWebhookSchema>

export async function verifyHmacSha256Signature(
  secret: string,
  rawBody: string,
  signature: string,
): Promise<boolean> {
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

  return constantTimeCompare(signature, expectedHex)
}

export async function processMessage(
  env: Bindings,
  tenantId: string,
  convId: string,
  userMessage: string,
  ctx: { platform: string; sender_id: string; access_token: string; [k: string]: string },
): Promise<void> {
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

async function sendZaloReply(token: string, userId: string, text: string): Promise<void> {
  await fetch('https://openapi.zalo.me/v3.0/oa/message/cs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'access_token': token },
    body: JSON.stringify({ recipient: { user_id: userId }, message: { text } }),
  })
}

async function sendFBReply(token: string, recipientId: string, text: string): Promise<void> {
  await fetch(`https://graph.facebook.com/v19.0/me/messages?access_token=${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipient: { id: recipientId }, message: { text } }),
  })
}
