/**
 * onboarding.ts — Beta onboarding flow for RaaS Gateway
 *
 * Core Flow (existing):
 * - GET  /status           — check current step and completion
 * - POST /profile          — step 1: business info
 * - POST /channel          — step 2: connect channel
 * - POST /menu             — step 3: upload menu + generate FAQs
 * - POST /activate         — step 4: complete onboarding
 *
 * Beta Flow (new):
 * - POST /signup           — initialize signup with email verification
 * - POST /verify-email     — verify email with code
 * - GET  /tutorial         — get tutorial progress
 * - POST /tutorial/step    — complete tutorial step
 * - GET  /usage            — get usage milestone status
 * - POST /feedback/nps     — submit NPS score
 * - POST /feedback         — submit general feedback
 * - GET  /feedback         — get feedback entries
 */
import { Hono } from 'hono'
import { z } from 'zod'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleDb, handleExternalApi } from '../types/error'
import {
  initializeOnboarding,
  verifyEmail,
  markWelcomeEmailSent,
  getOnboardingState,
  initializeTutorial,
  completeTutorialStep,
  getTutorialProgress,
  TUTORIAL_STEPS,
  updateUsageAndCheckMilestones,
  getUsageMilestoneStatus,
  markMilestoneEmailSent,
  submitNpsScore,
  submitFeedback,
  getFeedbackEntries,
  getAllFeedbackEntries,
  getAverageNpsScore,
  categorizeNpsScore,
} from '../onboarding/flows'
import {
  createWelcomeEmail,
  createVerificationEmail,
  createTutorialEmail,
  createMilestoneEmail,
  createFeedbackEmail,
} from '../emails/templates'

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

// Beta onboarding schemas
const signupSchema = z.object({
  email: z.string().email('Invalid email address'),
  business_name: z.string().min(1, 'Business name is required').max(200),
})

const verifyEmailSchema = z.object({
  code: z.string().length(6, 'Verification code must be 6 digits'),
})

const tutorialStepSchema = z.object({
  step_id: z.number().min(1).max(TUTORIAL_STEPS.length),
})

const npsSchema = z.object({
  score: z.number().min(0).max(10, 'NPS score must be between 0 and 10'),
})

const feedbackSchema = z.object({
  type: z.enum(['feature', 'general']),
  feedback: z.string().min(1, 'Feedback is required').max(2000),
  category: z.string().optional(),
})

export const onboardingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

onboardingRoutes.use('*', authMiddleware)

// GET /onboarding/status — return current step and completion flag
onboardingRoutes.get('/status', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const profile = await handleDb(
    async () => c.env.DB!.prepare(
      'SELECT onboarding_step, onboarding_completed FROM tenant_profiles WHERE tenant_id = ?'
    )
      .bind(tenant.id)
      .first() as Promise<{ onboarding_step: number; onboarding_completed: number } | null>,
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
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

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
    () => c.env.DB!.prepare(
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
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

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
    () => c.env.DB!.prepare(
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
    () => c.env.DB!.prepare(
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
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

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
    () => c.env.DB!.prepare(
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
      () => c.env.DB!.batch(kbInserts),
      'DATABASE_ERROR',
      'Failed to insert FAQ entries to knowledge base'
    )
  }

  return c.json({ step: 3, faq_generated: faqs.length, next: 'activate' })
}))

// POST /onboarding/activate — step 4: mark onboarding complete
onboardingRoutes.post('/activate', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const profile = await handleDb(
    async () => {
      const r = await c.env.DB!.prepare(
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
    () => c.env.DB!.prepare(
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

// ═══════════════════════════════════════════════════════════════
// BETA ONBOARDING FLOW — New Endpoints
// ═══════════════════════════════════════════════════════════════

// POST /onboarding/signup — initialize signup with email verification
onboardingRoutes.post('/signup', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  let body: z.infer<typeof signupSchema>
  try {
    body = signupSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  // Create tenant first
  const { createTenant } = await import('../raas/tenant')
  const { tenant, apiKey } = await createTenant(c.env.DB, body.business_name)

  // Initialize onboarding state
  const result = await initializeOnboarding(c.env.DB, tenant.id, body.email)
  if (!result.success) {
    return c.json(createError('INTERNAL_ERROR', result.error || 'Failed to initialize onboarding'), 500)
  }

  // Generate verification email template
  const verificationCode = generateVerificationCode()
  const origin = c.req.header('origin') || 'http://localhost:3000'
  const verificationUrl = `${origin}/v1/onboarding/verify?code=${verificationCode}`
  const emailTemplate = createVerificationEmail({
    email: body.email,
    verificationCode,
    verificationUrl,
  })

  // TODO: Send email via Resend/SendGrid/SES
  // For now, return the template for client to handle
  console.log('Verification email:', { to: body.email, subject: emailTemplate.subject })

  return c.json({
    tenant: { id: tenant.id, name: tenant.name, tier: tenant.tier },
    api_key: apiKey,
    email: body.email,
    email_template: emailTemplate,
    message: 'Signup successful. Please verify your email.',
  }, 201)
}))

// POST /onboarding/verify-email — verify email with code
onboardingRoutes.post('/verify-email', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant

  let body: z.infer<typeof verifyEmailSchema>
  try {
    body = verifyEmailSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const result = await verifyEmail(c.env.DB, tenant.id, body.code)
  if (!result.success) {
    return c.json(createError('BAD_REQUEST', result.error || 'Verification failed'), 400)
  }

  if (result.verified) {
    // Send welcome email template
    const state = await getOnboardingState(c.env.DB, tenant.id)
    const origin = c.req.header('origin') || 'http://localhost:3000'
    const welcomeTemplate = createWelcomeEmail({
      tenantName: tenant.name,
      businessName: tenant.name,
      apiKey: 'your-api-key', // Client should have this from signup
      dashboardUrl: `${origin}/dashboard`,
      docsUrl: 'https://docs.agencyos.network',
    })

    await markWelcomeEmailSent(c.env.DB, tenant.id)

    return c.json({
      verified: true,
      email_template: welcomeTemplate,
      message: 'Email verified. Welcome aboard!',
    })
  }

  return c.json({ verified: true, message: 'Email verified successfully' })
}))

// GET /onboarding/tutorial — get tutorial progress
onboardingRoutes.get('/tutorial', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant
  const state = await getOnboardingState(c.env.DB, tenant.id)

  if (!state) {
    // Initialize tutorial if no state exists
    await initializeTutorial(c.env.DB, tenant.id)
  }

  const progress = await getTutorialProgress(c.env.DB, tenant.id)

  return c.json({
    progress,
    steps: TUTORIAL_STEPS.map((step, index) => ({
      ...step,
      completed: progress ? index < progress.current_step - 1 : false,
      current: progress ? index === progress.current_step - 1 : false,
    })),
  })
}))

// POST /onboarding/tutorial/step — complete tutorial step
onboardingRoutes.post('/tutorial/step', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant

  let body: z.infer<typeof tutorialStepSchema>
  try {
    body = tutorialStepSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const result = await completeTutorialStep(c.env.DB, tenant.id, body.step_id)
  if (!result.success) {
    return c.json(createError('BAD_REQUEST', result.error || 'Failed to complete step'), 400)
  }

  let emailTemplate = null
  if (result.nextStep && !result.completed) {
    // Send tutorial step email
    const origin = c.req.header('origin') || 'http://localhost:3000'
    emailTemplate = createTutorialEmail({
      tenantName: tenant.name,
      tutorialStep: result.nextStep,
      totalSteps: TUTORIAL_STEPS.length,
      tutorialUrl: `${origin}/tutorial/step/${result.nextStep}`,
    })
  }

  return c.json({
    completed: result.completed,
    nextStep: result.nextStep,
    email_template: emailTemplate,
    message: result.completed
      ? 'Tutorial completed! 🎉'
      : `Step ${body.step_id} completed. Next: Step ${result.nextStep}`,
  })
}))

// GET /onboarding/usage — get usage milestone status
onboardingRoutes.get('/usage', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant
  const status = await getUsageMilestoneStatus(c.env.DB, tenant.id)

  if (!status) {
    // Initialize with default free tier
    const { initializeUsageTracking } = await import('../onboarding/flows')
    await initializeUsageTracking(c.env.DB, tenant.id, 'free', 200)
    return c.json({
      tier_name: 'free',
      tier_limit: 200,
      current_usage: 0,
      usage_percent: 0,
      milestone_reached: null,
      emails_sent: { milestone_10: false, milestone_50: false, milestone_80: false, milestone_100: false },
    })
  }

  return c.json(status)
}))

// POST /onboarding/usage/check — update usage and check milestones
onboardingRoutes.post('/usage/check', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant
  const { getBalance } = await import('../raas/credits')
  const currentUsage = await getBalance(c.env.DB, tenant.id)

  const result = await updateUsageAndCheckMilestones(c.env.DB, tenant.id, Math.abs(currentUsage))

  let emailTemplate = null
  if (result.shouldSendEmail && result.milestone) {
    const status = await getUsageMilestoneStatus(c.env.DB, tenant.id)
    const origin = c.req.header('origin') || 'http://localhost:3000'
    emailTemplate = createMilestoneEmail({
      tenantName: tenant.name,
      usagePercent: result.usagePercent,
      currentUsage: status?.current_usage || 0,
      tierLimit: status?.tier_limit || 200,
      tierName: status?.tier_name || 'free',
      upgradeUrl: `${origin}/billing/upgrade`,
    })

    await markMilestoneEmailSent(c.env.DB, tenant.id, result.milestone)
  }

  return c.json({
    usage_percent: result.usagePercent,
    milestone_reached: result.milestone,
    email_sent: result.shouldSendEmail,
    email_template: emailTemplate,
  })
}))

// POST /onboarding/feedback/nps — submit NPS score
onboardingRoutes.post('/feedback/nps', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant

  let body: z.infer<typeof npsSchema>
  try {
    body = npsSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const result = await submitNpsScore(c.env.DB, tenant.id, body.score)
  if (!result.success) {
    return c.json(createError('BAD_REQUEST', result.error || 'Failed to submit NPS score'), 400)
  }

  return c.json({
    success: true,
    score: body.score,
    category: categorizeNpsScore(body.score),
    message: 'Thank you for your feedback!',
  })
}))

// POST /onboarding/feedback — submit general feedback
onboardingRoutes.post('/feedback', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant

  let body: z.infer<typeof feedbackSchema>
  try {
    body = feedbackSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const result = await submitFeedback(c.env.DB, tenant.id, body.type, body.feedback, body.category)
  if (!result.success) {
    return c.json(createError('BAD_REQUEST', result.error || 'Failed to submit feedback'), 400)
  }

  return c.json({
    success: true,
    feedback_id: result.feedbackId,
    message: 'Feedback submitted. Thank you!',
  })
}))

// GET /onboarding/feedback — get feedback entries
onboardingRoutes.get('/feedback', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  const tenant = c.get('tenant') as Tenant
  const entries = await getFeedbackEntries(c.env.DB, tenant.id)
  const avgNps = await getAverageNpsScore(c.env.DB, tenant.id)

  return c.json({
    entries,
    average_nps: avgNps.average,
    nps_count: avgNps.count,
  })
}))

// GET /onboarding/feedback/all — get all feedback (admin only)
onboardingRoutes.get('/feedback/all', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

  // Check for admin/service token
  const authHeader = c.req.header('Authorization')
  if (!authHeader?.startsWith('Bearer ') || authHeader.slice(7) !== c.env.SERVICE_TOKEN) {
    return c.json(createError('UNAUTHORIZED', 'Service token required'), 401)
  }

  const entries = await getAllFeedbackEntries(c.env.DB, 100)
  const avgNps = await getAverageNpsScore(c.env.DB)

  return c.json({
    entries,
    average_nps: avgNps.average,
    nps_count: avgNps.count,
  })
}))

// Helper: Generate verification code
function generateVerificationCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString()
}
