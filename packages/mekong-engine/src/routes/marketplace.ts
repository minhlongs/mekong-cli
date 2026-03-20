import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { handleAsync, handleDb, createError, validateJsonBody } from '../types/error'
import { z } from 'zod'

type Variables = { tenant: Tenant }
const marketplaceRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
marketplaceRoutes.use('*', authMiddleware)

// Config schema validation - max depth 3, max 50 keys
const configSchemaItemSchema = z.object({
  type: z.enum(['string', 'number', 'boolean', 'select']),
  label: z.string().max(100),
  required: z.boolean().optional().default(false),
  default: z.unknown().optional(),
  options: z.array(z.string()).max(20).optional(),
})

const configSchemaSchema = z.record(configSchemaItemSchema).refine(
  (data) => Object.keys(data).length <= 50,
  'Config schema must have at most 50 keys'
)

// POST /v1/marketplace/plugins — publish a plugin
marketplaceRoutes.post('/plugins', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')

  // Define validation schema
  const pluginSchema = z.object({
    developer_id: z.string().uuid('developer_id must be a valid UUID'),
    name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
    slug: z.string().min(1, 'slug is required').max(100, 'slug must be ≤100 chars'),
    description: z.string().max(500, 'description must be ≤500 chars').optional(),
    category: z.string().max(100, 'category must be ≤100 chars').optional(),
    version: z.string().max(20, 'version must be ≤20 chars').optional().default('1.0.0'),
    pricing_type: z.enum(['free', 'paid', 'freemium']).optional().default('free'),
    price_credits: z.number().int().positive('price_credits must be positive').max(10_000, 'price too high').optional().default(0),
    webhook_url: z.string().url('webhook_url must be a valid URL').max(500, 'webhook_url too long').optional(),
    config_schema: configSchemaSchema.optional(),
  })

  let body: z.infer<typeof pluginSchema>
  try {
    body = pluginSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
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
}))

// GET /v1/marketplace/plugins — browse plugins, optional ?category=
marketplaceRoutes.get('/plugins', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const category = c.req.query('category')

  const query = category
    ? "SELECT * FROM marketplace_plugins WHERE status = 'published' AND category = ? ORDER BY install_count DESC LIMIT 50"
    : "SELECT * FROM marketplace_plugins WHERE status = 'published' ORDER BY install_count DESC LIMIT 50"
  const params = category ? [category] : []

  const result = await c.env.DB.prepare(query).bind(...params).all()
  return c.json({ plugins: result.results, total: result.results?.length || 0 })
}))

// POST /v1/marketplace/install — install plugin to tenant
marketplaceRoutes.post('/install', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')

  let body: { plugin_id: string; installed_by: string; config?: Record<string, unknown> }
  try {
    body = await c.req.json()
  } catch {
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  if (!body.plugin_id || !body.installed_by) {
    return c.json(createError('VALIDATION_ERROR', 'plugin_id and installed_by are required'), 400)
  }

  // Verify plugin exists and is published
  const plugin = await c.env.DB.prepare(
    "SELECT id, name FROM marketplace_plugins WHERE id = ? AND status = 'published'"
  )
    .bind(body.plugin_id)
    .first<{ id: string; name: string }>()
  if (!plugin) return c.json(createError('NOT_FOUND', 'Plugin not found or not published'), 404)

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.batch([
      c.env.DB.prepare(
        'INSERT INTO plugin_installs (id, plugin_id, tenant_id, installed_by, config) VALUES (?, ?, ?, ?, ?)'
      ).bind(id, body.plugin_id, tenant.id, body.installed_by, JSON.stringify(body.config || {})),
      c.env.DB.prepare(
        'UPDATE marketplace_plugins SET install_count = install_count + 1 WHERE id = ?'
      ).bind(body.plugin_id),
    ]),
    'DATABASE_ERROR',
    'Failed to install plugin'
  )

  return c.json(createError('OK', 'Plugin installed successfully', { install_id: id, plugin_name: plugin.name }), 201)
}))

// POST /v1/marketplace/review — rate a plugin (1-5)
marketplaceRoutes.post('/review', payloadSizeLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const body = await validateJsonBody(c, z.object({
    plugin_id: z.string().min(1, 'plugin_id is required'),
    reviewer_id: z.string().min(1, 'reviewer_id is required'),
    rating: z.number().int().min(1).max(5, 'rating must be between 1 and 5'),
    review_text: z.string().optional(),
  }))

  const { plugin_id, reviewer_id, rating, review_text } = body

  const id = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.prepare(
      'INSERT INTO plugin_reviews (id, plugin_id, reviewer_id, rating, review_text) VALUES (?, ?, ?, ?, ?)'
    )
      .bind(id, plugin_id, reviewer_id, rating, review_text || null)
      .run(),
    'DATABASE_ERROR',
    'Failed to submit review'
  )

  // Recalculate and update avg rating
  const stats = await c.env.DB.prepare(
    'SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM plugin_reviews WHERE plugin_id = ?'
  )
    .bind(plugin_id)
    .first<{ avg_rating: number; count: number }>()

  if (stats) {
    await handleDb(
      () => c.env.DB.prepare(
        'UPDATE marketplace_plugins SET rating_avg = ?, rating_count = ? WHERE id = ?'
      )
        .bind(stats.avg_rating, stats.count, plugin_id)
        .run(),
      'DATABASE_ERROR',
      'Failed to update plugin rating'
    )
  }

  return c.json({
    review_id: id,
    rating,
    new_avg: stats?.avg_rating?.toFixed(2) || rating.toFixed(2),
  }, 201)
}))

// GET /v1/marketplace/installed — list active installs for tenant
marketplaceRoutes.get('/installed', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const tenant = c.get('tenant')

  const result = await handleDb(
    () => c.env.DB.prepare(
      `SELECT pi.id, pi.plugin_id, pi.installed_by, pi.config, pi.installed_at,
            mp.name, mp.slug, mp.category, mp.version, mp.rating_avg
     FROM plugin_installs pi
     JOIN marketplace_plugins mp ON mp.id = pi.plugin_id
     WHERE pi.tenant_id = ? AND pi.status = 'active'
     ORDER BY pi.installed_at DESC`
    )
      .bind(tenant.id)
      .all(),
    'DATABASE_ERROR',
    'Failed to fetch installed plugins'
  )

  return c.json({ installed: result.results, total: result.results?.length || 0 })
}))

export { marketplaceRoutes }
