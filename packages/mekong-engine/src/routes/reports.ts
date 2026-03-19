/**
 * reports.ts — Analytics and reporting routes
 * GET /weekly   — 7-day aggregated stats + AI-generated summary
 * GET /overview — real-time dashboard metrics (today)
 */
import { Hono } from 'hono'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

type Variables = { tenant: Tenant }

export const reportRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

reportRoutes.use('*', authMiddleware)

// GET /reports/weekly — last 7 days aggregated + AI summary
reportRoutes.get('/weekly', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)

  const [messages, content, contacts, conversations] = await Promise.all([
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM messages
       WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
    ).bind(tenant.id).first<{ count: number }>(),

    c.env.DB.prepare(
      `SELECT status, COUNT(*) as count FROM content_posts
       WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')
       GROUP BY status`
    ).bind(tenant.id).all(),

    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM contacts
       WHERE tenant_id = ? AND first_contact_at >= datetime('now', '-7 days')`
    ).bind(tenant.id).first<{ count: number }>(),

    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM conversations
       WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
    ).bind(tenant.id).first<{ count: number }>(),
  ])

  const stats = {
    messages: messages?.count ?? 0,
    new_contacts: contacts?.count ?? 0,
    conversations: conversations?.count ?? 0,
    content: content.results,
  }

  const llm = new LLMClient({
    ai: c.env.AI,
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const summary = await llm.generate(
    `Business weekly report summary (be concise, 3 sentences max, in Vietnamese):
    - Messages handled: ${stats.messages}
    - New contacts: ${stats.new_contacts}
    - Conversations: ${stats.conversations}
    - Content posts: ${JSON.stringify(stats.content)}`
  )

  return c.json({ period: '7d', stats, ai_summary: summary })
})

// GET /reports/overview — real-time dashboard: today + totals
reportRoutes.get('/overview', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured', code: 'SERVICE_UNAVAILABLE' }, 503)

  const [todayMessages, totalContacts, pendingContent, activeConvs] = await Promise.all([
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM messages
       WHERE tenant_id = ? AND created_at >= datetime('now', 'start of day')`
    ).bind(tenant.id).first<{ count: number }>(),

    c.env.DB.prepare(
      'SELECT COUNT(*) as count FROM contacts WHERE tenant_id = ?'
    ).bind(tenant.id).first<{ count: number }>(),

    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM content_posts
       WHERE tenant_id = ? AND status IN ('draft','approved')`
    ).bind(tenant.id).first<{ count: number }>(),

    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM conversations
       WHERE tenant_id = ? AND status = 'active'`
    ).bind(tenant.id).first<{ count: number }>(),
  ])

  return c.json({
    today_messages: todayMessages?.count ?? 0,
    total_contacts: totalContacts?.count ?? 0,
    pending_content: pendingContent?.count ?? 0,
    active_conversations: activeConvs?.count ?? 0,
  })
})
