/**
 * crm.ts — Contact management + remarketing campaign routes
 * GET  /contacts          — list contacts with tag/limit filter
 * POST /contacts          — create contact manually
 * POST /contacts/auto     — upsert contact from chat event
 * GET  /campaigns         — list remarketing campaigns
 * POST /campaigns         — create campaign
 */
import { Hono } from 'hono'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { z } from 'zod'
import { handleAsync, handleDb, createError, ERROR_CODES } from '../types/error'

type Variables = { tenant: Tenant }

export const crmRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

// Zod schemas for CRM validation
const createContactSchema = z.object({
  external_id: z.string().optional(),
  platform: z.string().optional(),
  name: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
  tags: z.array(z.string()).optional(),
  notes: z.string().optional(),
})

const autoContactSchema = z.object({
  external_id: z.string().min(1, 'external_id is required'),
  platform: z.string().min(1, 'platform is required'),
  name: z.string().optional(),
})

const createCampaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required'),
  trigger_type: z.enum(['days_since_visit', 'birthday', 'manual', 'tag_match']),
  trigger_value: z.string().optional(),
  message_template: z.string().min(1, 'Message template is required'),
  channel: z.string().optional(),
})

crmRoutes.use('*', authMiddleware)

type Contact = {
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

// GET /crm/contacts — list with optional ?tag= and ?limit=
crmRoutes.get('/contacts', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tag = c.req.query('tag')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

  // Validate tag parameter to prevent SQL injection
  const TAG_PATTERN = /^[a-zA-Z0-9_-\s]+$/
  if (tag && !TAG_PATTERN.test(tag)) {
    return c.json(createError('VALIDATION_ERROR', 'Invalid tag format. Only alphanumeric, spaces, hyphens, and underscores allowed'), 400)
  }

  let contacts: Contact[]
  if (tag) {
    // Use LIKE with proper escaping instead of json_each for safety
    const escapedTag = tag.replace(/['"%]/g, '')
    const result = await handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          `SELECT * FROM contacts WHERE tenant_id = ? AND tags LIKE ? ORDER BY last_contact_at DESC LIMIT ?`
        )
          .bind(tenant.id, `%"${escapedTag}"%`, limit)
          .all()
        return r as { results?: Contact[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch contacts'
    )
    contacts = result.results || []
  } else {
    const result = await handleDb(
      async () => {
        const r = await c.env.DB.prepare(
          'SELECT * FROM contacts WHERE tenant_id = ? ORDER BY last_contact_at DESC LIMIT ?'
        )
          .bind(tenant.id, limit)
          .all()
        return r as { results?: Contact[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch contacts'
    )
    contacts = result.results || []
  }

  return c.json({ contacts, count: contacts.length })
}))

// POST /crm/contacts — create contact
crmRoutes.post('/contacts', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = createContactSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  const id = `ct_${tenant.id}_${Date.now()}`
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO contacts (id, tenant_id, external_id, platform, name, phone, email, tags, notes)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        id, tenant.id,
        parsed.data.external_id ?? null,
        parsed.data.platform ?? 'zalo',
        parsed.data.name ?? null,
        parsed.data.phone ?? null,
        parsed.data.email ?? null,
        JSON.stringify(parsed.data.tags ?? []),
        parsed.data.notes ?? null
      )
      .run(),
    'DATABASE_ERROR',
    'Failed to create contact'
  )

  return c.json({ id, created: true }, 201)
}))

// POST /crm/contacts/auto — upsert from chat event (platform + external_id key)
crmRoutes.post('/contacts/auto', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = autoContactSchema.safeParse(body)
  if (!parsed.success) {
    return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)
  }

  const existing = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT id, visit_count FROM contacts WHERE tenant_id = ? AND external_id = ? AND platform = ?'
      )
        .bind(tenant.id, body.external_id, body.platform)
        .first()
      return r as { id: string; visit_count: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch contact'
  )

  if (existing) {
    await handleDb(
      () => c.env.DB.prepare(
        `UPDATE contacts SET visit_count = visit_count + 1, last_contact_at = datetime('now')
       WHERE id = ?`
      )
        .bind(existing.id)
        .run(),
      'DATABASE_ERROR',
      'Failed to update contact'
    )
    return c.json({ id: existing.id, upserted: 'updated' })
  }

  const id = `ct_${tenant.id}_${Date.now()}`
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO contacts (id, tenant_id, external_id, platform, name)
     VALUES (?, ?, ?, ?, ?)`
    )
      .bind(id, tenant.id, body.external_id, body.platform, body.name ?? null)
      .run(),
    'DATABASE_ERROR',
    'Failed to create contact'
  )

  return c.json({ id, upserted: 'created' }, 201)
}))

// GET /crm/campaigns — list remarketing campaigns
crmRoutes.get('/campaigns', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const campaignsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT * FROM remarketing_campaigns WHERE tenant_id = ? ORDER BY created_at DESC'
      )
        .bind(tenant.id)
        .all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch campaigns'
  )

  return c.json({ campaigns: campaignsResult.results || [] })
}))

// POST /crm/campaigns — create campaign
crmRoutes.post('/campaigns', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = createCampaignSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  const id = `rc_${tenant.id}_${Date.now()}`
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO remarketing_campaigns (id, tenant_id, name, trigger_type, trigger_value, message_template, channel)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        id, tenant.id,
        parsed.data.name, parsed.data.trigger_type,
        parsed.data.trigger_value ?? null,
        parsed.data.message_template,
        parsed.data.channel ?? 'zalo'
      )
      .run(),
    'DATABASE_ERROR',
    'Failed to create campaign'
  )

  return c.json({ id, created: true }, 201)
}))
