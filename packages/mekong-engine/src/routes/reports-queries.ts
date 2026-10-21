import type { D1Database } from '@cloudflare/workers-types'
import { z } from 'zod'
import { handleDb } from '../types/error'

export const weeklyQuerySchema = z.object({
  days: z.string().optional().transform((val) => (val ? parseInt(val, 10) : 7)),
})

export const overviewQuerySchema = z.object({
  include_history: z.string().optional().transform((val) => val === 'true'),
})

export interface WeeklyStats {
  messages: number
  new_contacts: number
  conversations: number
  content?: Array<{ status: string; count: number }>
}

export interface OverviewResponse {
  today_messages: number
  total_contacts: number
  pending_content: number
  active_conversations: number
  history?: { messages_7d: number; contacts_7d: number }
}

export async function fetchWeeklyStats(db: D1Database, tenantId: string, days: number): Promise<WeeklyStats> {
  const [messagesResult, contentResult, contactsResult, conversationsResult] = await Promise.all([
    handleDb(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM messages
         WHERE tenant_id = ? AND created_at >= datetime('now', ? days')`
        ).bind(tenantId, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch messages count'
    ),
    handleDb(
      () => db.prepare(
        `SELECT status, COUNT(*) as count FROM content_posts
       WHERE tenant_id = ? AND created_at >= datetime('now', ? days')
       GROUP BY status`
      ).bind(tenantId, `-${days}`).all() as Promise<{ results?: Array<{ status: string; count: number }> }>,
      'DATABASE_ERROR',
      'Failed to fetch content stats'
    ),
    handleDb(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM contacts
         WHERE tenant_id = ? AND first_contact_at >= datetime('now', ? days')`
        ).bind(tenantId, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch contacts count'
    ),
    handleDb(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM conversations
         WHERE tenant_id = ? AND created_at >= datetime('now', ? days')`
        ).bind(tenantId, `-${days}`).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch conversations count'
    ),
  ])

  return {
    messages: messagesResult?.count ?? 0,
    new_contacts: contactsResult?.count ?? 0,
    conversations: conversationsResult?.count ?? 0,
    content: (contentResult as { results?: Array<{ status: string; count: number }> }).results,
  }
}

export async function fetchOverviewStats(
  db: D1Database,
  tenantId: string,
  includeHistory: boolean,
): Promise<OverviewResponse> {
  const [todayMessagesResult, totalContactsResult, pendingContentResult, activeConvsResult] = await Promise.all([
    handleDb<{ count: number } | null>(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM messages
         WHERE tenant_id = ? AND created_at >= datetime('now', 'start of day')`
        ).bind(tenantId).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch today messages'
    ),
    handleDb<{ count: number } | null>(
      async () => {
        const r = await db.prepare(
          'SELECT COUNT(*) as count FROM contacts WHERE tenant_id = ?'
        ).bind(tenantId).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch total contacts'
    ),
    handleDb<{ count: number } | null>(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM content_posts
         WHERE tenant_id = ? AND status IN ('draft','approved')`
        ).bind(tenantId).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch pending content'
    ),
    handleDb<{ count: number } | null>(
      async () => {
        const r = await db.prepare(
          `SELECT COUNT(*) as count FROM conversations
         WHERE tenant_id = ? AND status = 'active'`
        ).bind(tenantId).first()
        return r as { count: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch active conversations'
    ),
  ])

  const response: OverviewResponse = {
    today_messages: todayMessagesResult?.count ?? 0,
    total_contacts: totalContactsResult?.count ?? 0,
    pending_content: pendingContentResult?.count ?? 0,
    active_conversations: activeConvsResult?.count ?? 0,
  }

  if (includeHistory) {
    const [msg7dResult, contacts7dResult] = await Promise.all([
      handleDb<{ count: number } | null>(
        async () => {
          const r = await db.prepare(
            `SELECT COUNT(*) as count FROM messages
           WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
          ).bind(tenantId).first()
          return r as { count: number } | null
        },
        'DATABASE_ERROR',
        'Failed to fetch 7d messages'
      ),
      handleDb<{ count: number } | null>(
        async () => {
          const r = await db.prepare(
            `SELECT COUNT(*) as count FROM contacts
           WHERE tenant_id = ? AND first_contact_at >= datetime('now', '-7 days')`
          ).bind(tenantId).first()
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

  return response
}
