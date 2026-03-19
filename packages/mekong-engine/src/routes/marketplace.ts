import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'

type Variables = { tenant: Tenant }
const marketplaceRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
marketplaceRoutes.use('*', authMiddleware)

// POST /v1/marketplace/plugins — publish a plugin
marketplaceRoutes.post('/plugins', payloadSizeLimit(), async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: {
    developer_id: string
    name: string
    slug: string
    description?: string
    category?: string
    version?: string
    pricing_type?: string
    price_credits?: number
    webhook_url?: string
    config_schema?: Record<string, unknown>
  }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  if (!body.developer_id || !body.name || !body.slug) {
    return c.json({ error: 'developer_id, name, slug are required' }, 400)
  }

  const id = crypto.randomUUID()
  try {
    await c.env.DB.prepare(
      `INSERT INTO marketplace_plugins
        (id, developer_id, tenant_id, name, slug, description, category, version, pricing_type, price_credits, webhook_url, config_schema)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        id,
        body.developer_id,
        tenant.id,
        body.name,
        body.slug,
        body.description || null,
        body.category || 'integration',
        body.version || '1.0.0',
        body.pricing_type || 'free',
        body.price_credits || 0,
        body.webhook_url || null,
        JSON.stringify(body.config_schema || {}),
      )
      .run()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg.includes('UNIQUE')) return c.json({ error: 'Slug already exists', code: 'CONFLICT' }, 409)
    return c.json({ error: 'Failed to publish plugin' }, 500)
  }

  return c.json({ id, slug: body.slug, status: 'draft', message: 'Plugin published' }, 201)
})

// GET /v1/marketplace/plugins — browse plugins, optional ?category=
marketplaceRoutes.get('/plugins', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const category = c.req.query('category')

  const query = category
    ? "SELECT * FROM marketplace_plugins WHERE status = 'published' AND category = ? ORDER BY install_count DESC LIMIT 50"
    : "SELECT * FROM marketplace_plugins WHERE status = 'published' ORDER BY install_count DESC LIMIT 50"
  const params = category ? [category] : []

  const result = await c.env.DB.prepare(query).bind(...params).all()
  return c.json({ plugins: result.results, total: result.results?.length || 0 })
})

// POST /v1/marketplace/install — install plugin to tenant
marketplaceRoutes.post('/install', payloadSizeLimit(), async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  let body: { plugin_id: string; installed_by: string; config?: Record<string, unknown> }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  if (!body.plugin_id || !body.installed_by) {
    return c.json({ error: 'plugin_id and installed_by are required' }, 400)
  }

  // Verify plugin exists and is published
  const plugin = await c.env.DB.prepare(
    "SELECT id, name FROM marketplace_plugins WHERE id = ? AND status = 'published'"
  )
    .bind(body.plugin_id)
    .first<{ id: string; name: string }>()
  if (!plugin) return c.json({ error: 'Plugin not found or not published' }, 404)

  const id = crypto.randomUUID()
  try {
    await c.env.DB.batch([
      c.env.DB.prepare(
        'INSERT INTO plugin_installs (id, plugin_id, tenant_id, installed_by, config) VALUES (?, ?, ?, ?, ?)'
      ).bind(id, body.plugin_id, tenant.id, body.installed_by, JSON.stringify(body.config || {})),
      c.env.DB.prepare(
        'UPDATE marketplace_plugins SET install_count = install_count + 1 WHERE id = ?'
      ).bind(body.plugin_id),
    ])
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg.includes('UNIQUE')) return c.json({ error: 'Already installed', code: 'CONFLICT' }, 409)
    return c.json({ error: 'Failed to install plugin' }, 500)
  }

  return c.json({ install_id: id, plugin_name: plugin.name, status: 'active' }, 201)
})

// POST /v1/marketplace/review — rate a plugin (1-5)
marketplaceRoutes.post('/review', payloadSizeLimit(), async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  let body: { plugin_id: string; reviewer_id: string; rating: number; review_text?: string }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  if (!body.plugin_id || !body.reviewer_id || !body.rating) {
    return c.json({ error: 'plugin_id, reviewer_id, rating are required' }, 400)
  }
  if (body.rating < 1 || body.rating > 5) {
    return c.json({ error: 'rating must be between 1 and 5' }, 400)
  }

  const id = crypto.randomUUID()
  try {
    await c.env.DB.prepare(
      'INSERT INTO plugin_reviews (id, plugin_id, reviewer_id, rating, review_text) VALUES (?, ?, ?, ?, ?)'
    )
      .bind(id, body.plugin_id, body.reviewer_id, body.rating, body.review_text || null)
      .run()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg.includes('UNIQUE')) return c.json({ error: 'Already reviewed this plugin', code: 'CONFLICT' }, 409)
    return c.json({ error: 'Failed to submit review' }, 500)
  }

  // Recalculate and update avg rating
  const stats = await c.env.DB.prepare(
    'SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM plugin_reviews WHERE plugin_id = ?'
  )
    .bind(body.plugin_id)
    .first<{ avg_rating: number; count: number }>()

  if (stats) {
    await c.env.DB.prepare(
      'UPDATE marketplace_plugins SET rating_avg = ?, rating_count = ? WHERE id = ?'
    )
      .bind(stats.avg_rating, stats.count, body.plugin_id)
      .run()
  }

  return c.json({
    review_id: id,
    rating: body.rating,
    new_avg: stats?.avg_rating?.toFixed(2) || body.rating.toFixed(2),
  }, 201)
})

// GET /v1/marketplace/installed — list active installs for tenant
marketplaceRoutes.get('/installed', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')

  const result = await c.env.DB.prepare(
    `SELECT pi.id, pi.plugin_id, pi.installed_by, pi.config, pi.installed_at,
            mp.name, mp.slug, mp.category, mp.version, mp.rating_avg
     FROM plugin_installs pi
     JOIN marketplace_plugins mp ON mp.id = pi.plugin_id
     WHERE pi.tenant_id = ? AND pi.status = 'active'
     ORDER BY pi.installed_at DESC`
  )
    .bind(tenant.id)
    .all()

  return c.json({ installed: result.results, total: result.results?.length || 0 })
})

export { marketplaceRoutes }
