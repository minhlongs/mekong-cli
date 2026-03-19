/**
 * reports.ts — Analytics and reporting routes
 * GET /weekly   — 7-day aggregated stats + AI-generated summary
 * GET /overview — real-time dashboard metrics (today)
 */
import { Hono } from 'hono'
import { z } from 'zod'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleDb, handleExternalApi } from '../types/error'

type Variables = { tenant: Tenant }

// Zod schemas for query params
const weeklyQuerySchema = z.object({
  days: z.string().optional().transform((val) => (val ? parseInt(val, 10) : 7)),
})

const overviewQuerySchema = z.object({
  include_history: z.string().optional().transform((val) => val === 'true'),
})

export const reportRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

reportRoutes.use('*', authMiddleware)

// GET /reports/weekly — last 7 days aggregated + AI summary
reportRoutes.get('/weekly', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  // Validate query params
  let query: { days: number }
  try {
    query = weeklyQuerySchema.parse(c.req.query())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid query params', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid query params'), 400)
  }

  const days = Math.min(Math.max(query.days ?? 7, 1), 30) // 1-30 days range

  const [messagesResult, contentResult, contactsResult, conversationsResult] = await Promise.all([
    handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM messages
         WHERE tenant_id = ? AND created_at >= datetime('now', ? days')`
        ).bind(tenant.id, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch messages count'
    ),

    handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT status, COUNT(*) as count FROM content_posts
         WHERE tenant_id = ? AND created_at >= datetime('now', ? days')
         GROUP BY status`
        ).bind(tenant.id, `-${days}`).all()
        return r as { results?: Array<{ status: string; count: number }> }
      },
      'DATABASE_ERROR',
      'Failed to fetch content stats'
    ),

    handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM contacts
         WHERE tenant_id = ? AND first_contact_at >= datetime('now', ? days')`
        ).bind(tenant.id, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch contacts count'
    ),

    handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM conversations
         WHERE tenant_id = ? AND created_at >= datetime('now', ? days')`
        ).bind(tenant.id, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch conversations count'
    ),
  ])

  const stats = {
    messages: messagesResult?.count ?? 0,
    new_contacts: contactsResult?.count ?? 0,
    conversations: conversationsResult?.count ?? 0,
    content: (contentResult as { results?: Array<{ status: string; count: number }> }).results,
  }

  const llm = new LLMClient({
    ai: c.env.AI,
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const summary = await handleExternalApi(
    () => llm.generate(
      `Business weekly report summary (be concise, 3 sentences max, in Vietnamese):
      - Messages handled: ${stats.messages}
      - New contacts: ${stats.new_contacts}
      - Conversations: ${stats.conversations}
      - Content posts: ${JSON.stringify(stats.content)}`
    )
  )

  return c.json({ period: `${days}d`, stats, ai_summary: summary })
}))

// GET /reports/overview — real-time dashboard: today + totals
reportRoutes.get('/overview', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  // Validate query params
  let query: { include_history: boolean }
  try {
    query = overviewQuerySchema.parse(c.req.query())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid query params', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid query params'), 400)
  }

  const [todayMessagesResult, totalContactsResult, pendingContentResult, activeConvsResult] = await Promise.all([
    handleDb<{ count: number } | null>(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM messages
         WHERE tenant_id = ? AND created_at >= datetime('now', 'start of day')`
        ).bind(tenant.id).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch today messages'
    ),

    handleDb<{ count: number } | null>(
      async () => {
        const r = await c.env.DB.prepare(
          'SELECT COUNT(*) as count FROM contacts WHERE tenant_id = ?'
        ).bind(tenant.id).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch total contacts'
    ),

    handleDb<{ count: number } | null>(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM content_posts
         WHERE tenant_id = ? AND status IN ('draft','approved')`
        ).bind(tenant.id).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch pending content'
    ),

    handleDb<{ count: number } | null>(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT COUNT(*) as count FROM conversations
         WHERE tenant_id = ? AND status = 'active'`
        ).bind(tenant.id).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch active conversations'
    ),
  ])

  const response: {
    today_messages: number
    total_contacts: number
    pending_content: number
    active_conversations: number
    history?: { messages_7d: number; contacts_7d: number }
  } = {
    today_messages: todayMessagesResult?.count ?? 0,
    total_contacts: totalContactsResult?.count ?? 0,
    pending_content: pendingContentResult?.count ?? 0,
    active_conversations: activeConvsResult?.count ?? 0,
  }

  // Optional history if requested
  if (query.include_history) {
    const [msg7dResult, contacts7dResult] = await Promise.all([
      handleDb<{ count: number } | null>(
        async () => {
          const r = await c.env.DB.prepare(
            `SELECT COUNT(*) as count FROM messages
           WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
          ).bind(tenant.id).first()
          return r as { count: number } | null
        },
        'DATABASE_ERROR',
        'Failed to fetch 7d messages'
      ),
      handleDb<{ count: number } | null>(
        async () => {
          const r = await c.env.DB.prepare(
            `SELECT COUNT(*) as count FROM contacts
           WHERE tenant_id = ? AND first_contact_at >= datetime('now', '-7 days')`
          ).bind(tenant.id).first()
          return r as { count: number } | null
        },
        'DATABASE_ERROR',
        'Failed to fetch 7d contacts'
      ),
    ])
    response.history = {
      messages_7d: msg7dResult?.count ?? 0,
      contacts_7d: contacts7dResult?.count ?? 0,
    }
  }

  return c.json(response)
}))
