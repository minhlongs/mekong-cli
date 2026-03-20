/**
 * onboarding.ts — 4-step tenant onboarding flow
 * POST /profile   — step 1: business info
 * POST /channel   — step 2: connect Zalo/FB channel
 * POST /menu      — step 3: upload menu + auto-generate FAQ KB entries
 * POST /activate  — step 4: complete onboarding
 * GET  /status    — check current progress
 */
import { Hono } from 'hono'
import { z } from 'zod'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleDb, handleExternalApi } from '../types/error'

type Variables = { tenant: Tenant }

// Zod schemas
const profileSchema = z.object({
  business_name: z.string().min(1, 'business_name is required').max(200, 'business_name must be ≤200 chars'),
  industry: z.string().max(100, 'industry must be ≤100 chars').optional(),
  address: z.string().max(300, 'address must be ≤300 chars').optional(),
  phone: z.string().max(20, 'phone must be ≤20 chars').optional(),
  hours: z.string().max(200, 'hours must be ≤200 chars').optional(),
  logo_url: z.string().url('logo_url must be a valid URL').optional(),
})

const channelSchema = z.object({
  type: z.enum(['zalo_oa', 'facebook_page']),
  external_id: z.string().min(1, 'external_id is required').max(100, 'external_id must be ≤100 chars'),
  access_token: z.string().max(500, 'access_token must be ≤500 chars').optional(),
  name: z.string().max(200, 'name must be ≤200 chars').optional(),
})

const menuItemSchema = z.object({
  name: z.string().max(200, 'item name must be ≤200 chars'),
  price: z.number().positive('price must be positive').max(1_000_000, 'price too large'),
  description: z.string().max(500, 'description must be ≤500 chars').optional(),
  category: z.string().max(100, 'category must be ≤100 chars').optional(),
})

const menuSchema = z.object({
  menu_data: z.object({
    categories: z.array(z.string()).max(50, 'max 50 categories').optional(),
    items: z.array(menuItemSchema).max(500, 'max 500 items'),
  }).refine(data => {
    // Ensure total size is reasonable (100KB limit)
    return JSON.stringify(data).length < 100_000
  }, 'Menu data exceeds size limit (100KB)'),
})

type ProfileBody = z.infer<typeof profileSchema>
type ChannelBody = z.infer<typeof channelSchema>
type MenuBody = z.infer<typeof menuSchema>

export const onboardingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

onboardingRoutes.use('*', authMiddleware)

// GET /onboarding/status — return current step and completion flag
onboardingRoutes.get('/status', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const profile = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT onboarding_step, onboarding_completed FROM tenant_profiles WHERE tenant_id = ?'
      )
        .bind(tenant.id)
        .first()
      return r as { onboarding_step: number; onboarding_completed: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch onboarding status'
  )

  return c.json({
    step: profile?.onboarding_step ?? 0,
    completed: !!profile?.onboarding_completed,
    steps: ['profile', 'channel', 'menu', 'activate'],
  })
}))

// POST /onboarding/profile — step 1: save business info
onboardingRoutes.post('/profile', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: ProfileBody
  try {
    body = profileSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO tenant_profiles (tenant_id, business_name, industry, address, phone, hours, logo_url, onboarding_step)
       VALUES (?, ?, ?, ?, ?, ?, ?, 1)
       ON CONFLICT(tenant_id) DO UPDATE SET
         business_name = excluded.business_name,
         industry = excluded.industry,
         address = excluded.address,
         phone = excluded.phone,
         hours = excluded.hours,
         logo_url = excluded.logo_url,
         onboarding_step = MAX(onboarding_step, 1),
         updated_at = datetime('now')`
    )
      .bind(
        tenant.id,
        body.business_name,
        body.industry ?? 'cafe',
        body.address ?? null,
        body.phone ?? null,
        body.hours ?? null,
        body.logo_url ?? null
      )
      .run(),
    'DATABASE_ERROR',
    'Failed to save business profile'
  )

  return c.json({ step: 1, next: 'channel' })
}))

// POST /onboarding/channel — step 2: record channel connection intent
onboardingRoutes.post('/channel', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: ChannelBody
  try {
    body = channelSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const channelId = `ch_${tenant.id}_${body.type}`
  await handleDb(
    () => c.env.DB.prepare(
      `INSERT INTO channels (id, tenant_id, type, external_id, name, access_token_encrypted, active)
       VALUES (?, ?, ?, ?, ?, ?, 1)
       ON CONFLICT(id) DO UPDATE SET
         external_id = excluded.external_id,
         name = excluded.name,
         access_token_encrypted = excluded.access_token_encrypted,
         active = 1`
    )
      .bind(channelId, tenant.id, body.type, body.external_id, body.name ?? null, body.access_token ?? null)
      .run(),
    'DATABASE_ERROR',
    'Failed to save channel connection'
  )

  await handleDb(
    () => c.env.DB.prepare(
      `UPDATE tenant_profiles SET onboarding_step = MAX(onboarding_step, 2), updated_at = datetime('now')
       WHERE tenant_id = ?`
    )
      .bind(tenant.id)
      .run(),
    'DATABASE_ERROR',
    'Failed to update onboarding step'
  )

  return c.json({ step: 2, channel_id: channelId, next: 'menu' })
}))

// POST /onboarding/menu — step 3: store menu + generate FAQ KB entries
onboardingRoutes.post('/menu', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: MenuBody
  try {
    body = menuSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  await handleDb(
    () => c.env.DB.prepare(
      `UPDATE tenant_profiles
       SET menu_data = ?, onboarding_step = MAX(onboarding_step, 3), updated_at = datetime('now')
       WHERE tenant_id = ?`
    )
      .bind(JSON.stringify(body.menu_data), tenant.id)
      .run(),
    'DATABASE_ERROR',
    'Failed to save menu data'
  )

  const llm = new LLMClient({
    ai: c.env.AI,
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const faqPrompt = `Given this cafe menu: ${JSON.stringify(body.menu_data).slice(0, 1000)}
Generate 5 FAQ Q&A pairs customers commonly ask. Return JSON: [{"question":"...","answer":"..."}]`

  let faqs: Array<{ question: string; answer: string }> = []
  try {
    const result = await handleExternalApi(
      () => llm.generateJson(faqPrompt)
    )
    faqs = Array.isArray(result) ? result : []
  } catch {
    // non-blocking — menu saved, FAQ generation optional
  }

  const kbInserts = faqs.map((faq) => {
    const id = `kb_${tenant.id}_faq_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
    return c.env.DB!.prepare(
      `INSERT OR IGNORE INTO knowledge_base (id, tenant_id, title, content, category)
       VALUES (?, ?, ?, ?, 'faq')`
    ).bind(id, tenant.id, faq.question, faq.answer)
  })

  if (kbInserts.length > 0) {
    await handleDb(
      () => c.env.DB.batch(kbInserts),
      'DATABASE_ERROR',
      'Failed to insert FAQ entries to knowledge base'
    )
  }

  return c.json({ step: 3, faq_generated: faqs.length, next: 'activate' })
}))

// POST /onboarding/activate — step 4: mark onboarding complete
onboardingRoutes.post('/activate', handleAsync(async (c) => {
  const tenant = c.get('tenant')

  const profile = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT onboarding_step FROM tenant_profiles WHERE tenant_id = ?'
      )
        .bind(tenant.id)
        .first()
      return r as { onboarding_step: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch onboarding profile'
  )

  if (!profile || profile.onboarding_step < 3) {
    return c.json(createError('BAD_REQUEST', 'Complete steps 1-3 before activating'), 400)
  }

  await handleDb(
    () => c.env.DB.prepare(
      `UPDATE tenant_profiles
       SET onboarding_step = 4, onboarding_completed = 1, updated_at = datetime('now')
       WHERE tenant_id = ?`
    )
      .bind(tenant.id)
      .run(),
    'DATABASE_ERROR',
    'Failed to activate tenant'
  )

  return c.json({ step: 4, completed: true, message: 'Onboarding complete. System is active.' })
}))
