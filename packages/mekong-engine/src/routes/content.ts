/**
 * content.ts — AI content generation + scheduling routes
 * POST /generate  — batch 7-14 day content via LLM, saved as drafts
 * GET  /          — list posts with optional status filter
 * PATCH /:id      — approve/reject/edit a post
 */
import { Hono } from 'hono'
import { z } from 'zod'
import type { D1PreparedStatement } from '@cloudflare/workers-types'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { LLMClient } from '../core/llm-client'
import { handleAsync, handleDb, requireResource, createError } from '../types/error'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

type Variables = { tenant: Tenant }

// Zod schemas for content operations
const generateContentSchema = z.object({
  channel: z.string().optional().default('facebook'),
  days: z.number().min(7).max(14).optional().default(7),
  industry: z.string().optional().default('cafe'),
  topic: z.string().optional().default('daily promotions'),
})

const updatePostSchema = z.object({
  status: z.enum(['approved', 'rejected', 'scheduled']).optional(),
  content_text: z.string().optional(),
  scheduled_at: z.string().optional(),
})

type GenerateContentBody = z.infer<typeof generateContentSchema>
type UpdatePostBody = z.infer<typeof updatePostSchema>

export const contentRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

contentRoutes.use('*', authMiddleware)

// POST /content/generate — LLM generates 7-14 day content batch as drafts
contentRoutes.post('/generate', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  let body: GenerateContentBody
  try {
    body = generateContentSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const channel = body.channel ?? 'facebook'
  const days = Math.min(Math.max(body.days ?? 7, 7), 14)
  const industry = body.industry ?? 'cafe'
  const topic = body.topic ?? 'daily promotions'

  const llm = new LLMClient({
    ai: c.env.AI,
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const prompt = `Generate ${days} social media posts for a ${industry} business on ${channel}.
Topic focus: ${topic}. Each post should be engaging, include emojis, and be suitable for Vietnamese audiences.
Return JSON array: [{ "day": 1, "content_text": "...", "image_prompt": "..." }, ...]`

  let posts: Array<{ day: number; content_text: string; image_prompt?: string }> = []
  try {
    const result = await llm.generateJson(prompt)
    posts = Array.isArray(result) ? result : (result.posts as typeof posts) ?? []
  } catch {
    return c.json(createError('SERVICE_UNAVAILABLE', 'LLM generation failed'), 502)
  }

  const now = new Date()
  const inserted: string[] = []

  for (const post of posts) {
    const id = `cp_${tenant.id}_${Date.now()}_${post.day}`
    const scheduledAt = new Date(now)
    scheduledAt.setDate(scheduledAt.getDate() + (post.day - 1))

    await handleDb(
      () => c.env.DB!.prepare(
        `INSERT INTO content_posts (id, tenant_id, channel, content_text, image_prompt, status, scheduled_at)
       VALUES (?, ?, ?, ?, ?, 'draft', ?)`
      )
        .bind(id, tenant.id, channel, post.content_text, post.image_prompt ?? null, scheduledAt.toISOString())
        .run(),
      'DATABASE_ERROR',
      'Failed to save generated content'
    )

    inserted.push(id)
  }

  return c.json({ generated: inserted.length, ids: inserted })
}))

// GET /content — list posts, optional ?status= filter
contentRoutes.get('/', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const status = c.req.query('status')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 100)

  let query: D1PreparedStatement
  if (status) {
    query = c.env.DB!.prepare(
      'SELECT * FROM content_posts WHERE tenant_id = ? AND status = ? ORDER BY scheduled_at ASC LIMIT ?'
    ).bind(tenant.id, status, limit)
  } else {
    query = c.env.DB!.prepare(
      'SELECT * FROM content_posts WHERE tenant_id = ? ORDER BY scheduled_at ASC LIMIT ?'
    ).bind(tenant.id, limit)
  }

  const { results } = await handleDb(
    () => query.all(),
    'DATABASE_ERROR',
    'Failed to fetch content posts'
  )
  return c.json({ posts: results, count: results.length })
}))

// PATCH /content/:id — approve/reject/edit
contentRoutes.patch('/:id', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const id = c.req.param('id')

  let body: UpdatePostBody
  try {
    body = updatePostSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const existing = await handleDb(
    () => c.env.DB!.prepare(
      'SELECT id FROM content_posts WHERE id = ? AND tenant_id = ?'
    )
      .bind(id, tenant.id)
      .first(),
    'DATABASE_ERROR',
    'Failed to fetch post'
  )

  if (!existing) return c.json(createError('NOT_FOUND', 'Post not found'), 404)

  const fields: string[] = []
  const values: unknown[] = []

  if (body.status) { fields.push('status = ?'); values.push(body.status) }
  if (body.content_text) { fields.push('content_text = ?'); values.push(body.content_text) }
  if (body.scheduled_at) { fields.push('scheduled_at = ?'); values.push(body.scheduled_at) }

  if (fields.length === 0) return c.json(createError('BAD_REQUEST', 'No fields to update'), 400)

  values.push(id, tenant.id)
  await handleDb(
    () => c.env.DB!.prepare(
      `UPDATE content_posts SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`
    )
      .bind(...values)
      .run(),
    'DATABASE_ERROR',
    'Failed to update post'
  )

  return c.json({ updated: true })
}))
