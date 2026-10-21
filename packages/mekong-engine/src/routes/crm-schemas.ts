import type { D1Database } from '@cloudflare/workers-types'
import { z } from 'zod'
import { handleDb } from '../types/error'

export const createContactSchema = z.object({
  external_id: z.string().optional(),
  platform: z.string().optional(),
  name: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
  tags: z.array(z.string()).optional(),
  notes: z.string().optional(),
})

export const autoContactSchema = z.object({
  external_id: z.string().min(1, 'external_id is required'),
  platform: z.string().min(1, 'platform is required'),
  name: z.string().optional(),
})

export const createCampaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required'),
  trigger_type: z.enum(['days_since_visit', 'birthday', 'manual', 'tag_match']),
  trigger_value: z.string().optional(),
  message_template: z.string().min(1, 'Message template is required'),
  channel: z.string().optional(),
})

export type Contact = {
  id: string
  tenant_id: string
  external_id: string | null
  platform: string
  name: string | null
  phone: string | null
  email: string | null
  tags: string
  notes: string | null
  visit_count: number
  last_contact_at: string
  created_at: string
  updated_at: string
}

export type Campaign = {
  id: string
  tenant_id: string
  name: string
  trigger_type: string
  trigger_value: string | null
  message_template: string
  channel: string | null
  created_at: string
}

export const TAG_PATTERN = /^[a-zA-Z0-9_-\s]+$/

export async function queryContacts(
  db: D1Database,
  tenantId: string,
  limit: number,
  tag?: string,
): Promise<Contact[]> {
  if (tag) {
    const escapedTag = tag.replace(/['"%]/g, '')
    const result = await handleDb(
      async () => {
        const r = await db
          .prepare('SELECT * FROM contacts WHERE tenant_id = ? AND tags LIKE ? ORDER BY last_contact_at DESC LIMIT ?')
          .bind(tenantId, `%"${escapedTag}"%`, limit)
          .all()
        return r as unknown as { results?: Contact[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch contacts'
    )
    return result.results || []
  }

  const result = await handleDb(
    async () => {
      const r = await db
        .prepare('SELECT * FROM contacts WHERE tenant_id = ? ORDER BY last_contact_at DESC LIMIT ?')
        .bind(tenantId, limit)
        .all()
      return r as unknown as { results?: Contact[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch contacts'
  )
  return result.results || []
}

export async function upsertContactFromEvent(
  db: D1Database,
  tenantId: string,
  externalId: string,
  platform: string,
  name?: string,
): Promise<{ id: string; upserted: 'updated' | 'created' }> {
  const existing = await handleDb(
    async () => {
      const r = await db
        .prepare('SELECT id, visit_count FROM contacts WHERE tenant_id = ? AND external_id = ? AND platform = ?')
        .bind(tenantId, externalId, platform)
        .first()
      return r as { id: string; visit_count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch contact'
  )

  if (existing) {
    await handleDb(
      () => db
        .prepare("UPDATE contacts SET visit_count = visit_count + 1, last_contact_at = datetime('now') WHERE id = ?")
        .bind(existing.id)
        .run(),
      'DATABASE_ERROR',
      'Failed to update contact'
    )
    return { id: existing.id, upserted: 'updated' }
  }

  const id = `ct_${tenantId}_${Date.now()}`
  await handleDb(
    () => db
      .prepare('INSERT INTO contacts (id, tenant_id, external_id, platform, name) VALUES (?, ?, ?, ?, ?)')
      .bind(id, tenantId, externalId, platform, name ?? null)
      .run(),
    'DATABASE_ERROR',
    'Failed to create contact'
  )

  return { id, upserted: 'created' }
}
