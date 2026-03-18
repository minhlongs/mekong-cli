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
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

type Variables = { tenant: Tenant }

export const crmRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

crmRoutes.use('*', authMiddleware)

// GET /crm/contacts — list with optional ?tag= and ?limit=
crmRoutes.get('/contacts', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const tag = c.req.query('tag')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

  let contacts
  if (tag) {
    const { results } = await c.env.DB.prepare(
      `SELECT * FROM contacts WHERE tenant_id = ? AND json_each.value = ? LIMIT ?`
    )
      .bind(tenant.id, tag, limit)
      .all()
    contacts = results
  } else {
    const { results } = await c.env.DB.prepare(
      'SELECT * FROM contacts WHERE tenant_id = ? ORDER BY last_contact_at DESC LIMIT ?'
    )
      .bind(tenant.id, limit)
      .all()
    contacts = results
  }

  return c.json({ contacts, count: contacts.length })
})

// POST /crm/contacts — create contact
crmRoutes.post('/contacts', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    external_id?: string
    platform?: string
    name?: string
    phone?: string
    email?: string
    tags?: string[]
    notes?: string
  }>()

  const id = `ct_${tenant.id}_${Date.now()}`
  await c.env.DB.prepare(
    `INSERT INTO contacts (id, tenant_id, external_id, platform, name, phone, email, tags, notes)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  )
    .bind(
      id, tenant.id,
      body.external_id ?? null,
      body.platform ?? 'zalo',
      body.name ?? null,
      body.phone ?? null,
      body.email ?? null,
      JSON.stringify(body.tags ?? []),
      body.notes ?? null
    )
    .run()

  return c.json({ id, created: true }, 201)
})

// POST /crm/contacts/auto — upsert from chat event (platform + external_id key)
crmRoutes.post('/contacts/auto', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    external_id: string
    platform: string
    name?: string
  }>()

  if (!body.external_id || !body.platform) {
    return c.json({ error: 'external_id and platform required' }, 400)
  }

  const existing = await c.env.DB.prepare(
    'SELECT id, visit_count FROM contacts WHERE tenant_id = ? AND external_id = ? AND platform = ?'
  )
    .bind(tenant.id, body.external_id, body.platform)
    .first<{ id: string; visit_count: number }>()

  if (existing) {
    await c.env.DB.prepare(
      `UPDATE contacts SET visit_count = visit_count + 1, last_contact_at = datetime('now')
       WHERE id = ?`
    )
      .bind(existing.id)
      .run()
    return c.json({ id: existing.id, upserted: 'updated' })
  }

  const id = `ct_${tenant.id}_${Date.now()}`
  await c.env.DB.prepare(
    `INSERT INTO contacts (id, tenant_id, external_id, platform, name)
     VALUES (?, ?, ?, ?, ?)`
  )
    .bind(id, tenant.id, body.external_id, body.platform, body.name ?? null)
    .run()

  return c.json({ id, upserted: 'created' }, 201)
})

// GET /crm/campaigns — list remarketing campaigns
crmRoutes.get('/campaigns', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const { results } = await c.env.DB.prepare(
    'SELECT * FROM remarketing_campaigns WHERE tenant_id = ? ORDER BY created_at DESC'
  )
    .bind(tenant.id)
    .all()

  return c.json({ campaigns: results })
})

// POST /crm/campaigns — create campaign
crmRoutes.post('/campaigns', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    name: string
    trigger_type: 'days_since_visit' | 'birthday' | 'manual' | 'tag_match'
    trigger_value?: string
    message_template: string
    channel?: string
  }>()

  if (!body.name || !body.trigger_type || !body.message_template) {
    return c.json({ error: 'name, trigger_type, message_template required' }, 400)
  }

  const id = `rc_${tenant.id}_${Date.now()}`
  await c.env.DB.prepare(
    `INSERT INTO remarketing_campaigns (id, tenant_id, name, trigger_type, trigger_value, message_template, channel)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  )
    .bind(
      id, tenant.id,
      body.name, body.trigger_type,
      body.trigger_value ?? null,
      body.message_template,
      body.channel ?? 'zalo'
    )
    .run()

  return c.json({ id, created: true }, 201)
})
