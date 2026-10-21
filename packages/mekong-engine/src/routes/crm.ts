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
import { handleAsync, handleDb, createError } from '../types/error'
import {
  createContactSchema,
  autoContactSchema,
  createCampaignSchema,
  type Campaign,
  TAG_PATTERN,
  queryContacts,
  upsertContactFromEvent,
} from './crm-schemas'

type Variables = { tenant: Tenant }

export const crmRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

crmRoutes.use('*', authMiddleware)

// GET /crm/contacts — list with optional ?tag= and ?limit=
crmRoutes.get('/contacts', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tag = c.req.query('tag')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

  if (tag && !TAG_PATTERN.test(tag)) {
    return c.json(createError('VALIDATION_ERROR', 'Invalid tag format. Only alphanumeric, spaces, hyphens, and underscores allowed'), 400)
  }

  const contacts = await queryContacts(c.env.DB, tenant.id, limit, tag)
  return c.json({ contacts, count: contacts.length })
}))

// POST /crm/contacts — create contact
crmRoutes.post('/contacts', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = createContactSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  const id = `ct_${tenant.id}_${Date.now()}`
  await handleDb(
    () => c.env.DB!.prepare(
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
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = autoContactSchema.safeParse(body)
  if (!parsed.success) {
    return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)
  }

  const result = await upsertContactFromEvent(
    c.env.DB,
    tenant.id,
    body.external_id,
    body.platform,
    body.name
  )

  return c.json(result, result.upserted === 'created' ? 201 : 200)
}))

// GET /crm/campaigns — list remarketing campaigns
crmRoutes.get('/campaigns', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const campaignsResult = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
        'SELECT * FROM remarketing_campaigns WHERE tenant_id = ? ORDER BY created_at DESC'
      )
        .bind(tenant.id)
        .all()
      return r as unknown as { results?: Campaign[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch campaigns'
  )

  return c.json({ campaigns: campaignsResult.results || [] })
}))

// POST /crm/campaigns — create campaign
crmRoutes.post('/campaigns', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await c.req.json()
  const parsed = createCampaignSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  const id = `rc_${tenant.id}_${Date.now()}`
  await handleDb(
    () => c.env.DB!.prepare(
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
