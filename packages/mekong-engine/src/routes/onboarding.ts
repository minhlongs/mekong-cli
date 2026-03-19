/**
 * onboarding.ts — 4-step tenant onboarding flow
 * POST /profile   — step 1: business info
 * POST /channel   — step 2: connect Zalo/FB channel
 * POST /menu      — step 3: upload menu + auto-generate FAQ KB entries
 * POST /activate  — step 4: complete onboarding
 * GET  /status    — check current progress
 */
import { Hono } from 'hono'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

type Variables = { tenant: Tenant }

export const onboardingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

onboardingRoutes.use('*', authMiddleware)

// GET /onboarding/status — return current step and completion flag
onboardingRoutes.get('/status', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const profile = await c.env.DB.prepare(
    'SELECT onboarding_step, onboarding_completed FROM tenant_profiles WHERE tenant_id = ?'
  )
    .bind(tenant.id)
    .first<{ onboarding_step: number; onboarding_completed: number }>()

  return c.json({
    step: profile?.onboarding_step ?? 0,
    completed: !!profile?.onboarding_completed,
    steps: ['profile', 'channel', 'menu', 'activate'],
  })
})

// POST /onboarding/profile — step 1: save business info
onboardingRoutes.post('/profile', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    business_name: string
    industry?: string
    address?: string
    phone?: string
    hours?: string
    logo_url?: string
  }>()

  if (!body.business_name) return c.json({ error: 'business_name required' }, 400)

  await c.env.DB.prepare(
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
    .run()

  return c.json({ step: 1, next: 'channel' })
})

// POST /onboarding/channel — step 2: record channel connection intent
onboardingRoutes.post('/channel', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    type: 'zalo_oa' | 'facebook_page'
    external_id: string
    access_token?: string
    name?: string
  }>()

  if (!body.type || !body.external_id) {
    return c.json({ error: 'type and external_id required' }, 400)
  }

  const channelId = `ch_${tenant.id}_${body.type}`
  await c.env.DB.prepare(
    `INSERT INTO channels (id, tenant_id, type, external_id, name, access_token_encrypted, active)
     VALUES (?, ?, ?, ?, ?, ?, 1)
     ON CONFLICT(id) DO UPDATE SET
       external_id = excluded.external_id,
       name = excluded.name,
       access_token_encrypted = excluded.access_token_encrypted,
       active = 1`
  )
    .bind(channelId, tenant.id, body.type, body.external_id, body.name ?? null, body.access_token ?? null)
    .run()

  await c.env.DB.prepare(
    `UPDATE tenant_profiles SET onboarding_step = MAX(onboarding_step, 2), updated_at = datetime('now')
     WHERE tenant_id = ?`
  )
    .bind(tenant.id)
    .run()

  return c.json({ step: 2, channel_id: channelId, next: 'menu' })
})

// POST /onboarding/menu — step 3: store menu + generate FAQ KB entries
onboardingRoutes.post('/menu', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const body = await c.req.json<{
    menu_data: Record<string, unknown>
  }>()

  if (!body.menu_data) return c.json({ error: 'menu_data required' }, 400)

  await c.env.DB.prepare(
    `UPDATE tenant_profiles
     SET menu_data = ?, onboarding_step = MAX(onboarding_step, 3), updated_at = datetime('now')
     WHERE tenant_id = ?`
  )
    .bind(JSON.stringify(body.menu_data), tenant.id)
    .run()

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
    const result = await llm.generateJson(faqPrompt)
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
    await c.env.DB.batch(kbInserts)
  }

  return c.json({ step: 3, faq_generated: faqs.length, next: 'activate' })
})

// POST /onboarding/activate — step 4: mark onboarding complete
onboardingRoutes.post('/activate', async (c) => {
  const tenant = c.get('tenant')
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const profile = await c.env.DB.prepare(
    'SELECT onboarding_step FROM tenant_profiles WHERE tenant_id = ?'
  )
    .bind(tenant.id)
    .first<{ onboarding_step: number }>()

  if (!profile || profile.onboarding_step < 3) {
    return c.json({ error: 'Complete steps 1-3 before activating' }, 400)
  }

  await c.env.DB.prepare(
    `UPDATE tenant_profiles
     SET onboarding_step = 4, onboarding_completed = 1, updated_at = datetime('now')
     WHERE tenant_id = ?`
  )
    .bind(tenant.id)
    .run()

  return c.json({ step: 4, completed: true, message: 'Onboarding complete. System is active.' })
})
