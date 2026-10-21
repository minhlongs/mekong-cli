/**
 * Onboarding Activation, Signup, Email Verification & Tutorial Route Handlers
 */

import type { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleDb } from '../types/error'
import {
  initializeOnboarding,
  verifyEmail,
  markWelcomeEmailSent,
  getOnboardingState,
  initializeTutorial,
  completeTutorialStep,
  getTutorialProgress,
  TUTORIAL_STEPS,
} from '../onboarding/flows'
import {
  createWelcomeEmail,
  createVerificationEmail,
  createTutorialEmail,
} from '../emails/templates'
import {
  type Variables,
  signupSchema,
  verifyEmailSchema,
  tutorialStepSchema,
  generateVerificationCode,
} from './onboarding-schemas'

export function registerBetaOnboardingStatus(
  app: Hono<{ Bindings: Bindings; Variables: Variables }>
): void {
  // POST /onboarding/activate — step 4: mark onboarding complete
  app.post('/activate', handleAsync(async (c) => {
    const tenant = c.get('tenant') as Tenant
    if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

    const profile = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(
          'SELECT onboarding_step FROM tenant_profiles WHERE tenant_id = ?'
        ).bind(tenant.id).first()
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
      ).bind(tenant.id).run(),
      'DATABASE_ERROR',
      'Failed to activate tenant'
    )

    return c.json({ step: 4, completed: true, message: 'Onboarding complete. System is active.' })
  }))

  // POST /onboarding/signup — initialize signup with email verification
  app.post('/signup', handleAsync(async (c) => {
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

    let tenant: Tenant
    let apiKey: string

    const {
      PilotInviteError,
      isPilotModeEnabled,
      redeemInviteAndCreateTenant,
    } = await import('../raas/invite-codes')

    let redeemedInviteId: string | undefined
    if (isPilotModeEnabled(c.env.PILOT_MODE)) {
      try {
        const redeemed = await redeemInviteAndCreateTenant(c.env.DB, body.invite_code, body.business_name)
        tenant = redeemed.tenant
        apiKey = redeemed.apiKey
        redeemedInviteId = redeemed.inviteId
      } catch (err) {
        if (err instanceof PilotInviteError) {
          const errorCode = err.statusCode === 409 ? 'CONFLICT' : 'FORBIDDEN'
          return c.json({ ...createError(errorCode, err.message), invite_error_code: err.code }, err.statusCode)
        }
        throw err
      }
    } else {
      const { createTenant } = await import('../raas/tenant')
      const created = await createTenant(c.env.DB, body.business_name)
      tenant = created.tenant
      apiKey = created.apiKey
    }

    const result = await initializeOnboarding(c.env.DB, tenant.id, body.email)
    if (!result.success) {
      if (redeemedInviteId) {
        await c.env.DB
          .prepare("UPDATE pilot_invites SET status = 'active', redeemed_by_tenant_id = NULL, redeemed_at = NULL WHERE id = ?")
          .bind(redeemedInviteId)
          .run()
          .catch(() => {})
      }
      return c.json(createError('INTERNAL_ERROR', result.error || 'Failed to initialize onboarding'), 500)
    }

    const verificationCode = generateVerificationCode()
    const origin = c.req.header('origin') || 'https://ide.mekongmind.com'
    const emailTemplate = createVerificationEmail({
      email: body.email,
      verificationCode,
      verificationUrl: `${origin}/v1/onboarding/verify?code=${verificationCode}`,
    })

    return c.json({
      tenant: { id: tenant.id, name: tenant.name, tier: tenant.tier },
      api_key: apiKey,
      email: body.email,
      email_template: emailTemplate,
      message: 'Signup successful. Save your API key now — it is returned only once.',
    }, 201)
  }))

  // POST /onboarding/verify-email — verify email with code
  app.post('/verify-email', handleAsync(async (c) => {
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
      await getOnboardingState(c.env.DB, tenant.id)
      const origin = c.req.header('origin') || 'http://localhost:3000'
      const welcomeTemplate = createWelcomeEmail({
        tenantName: tenant.name,
        businessName: tenant.name,
        apiKey: 'your-api-key',
        dashboardUrl: `${origin}/dashboard`,
        docsUrl: 'https://www.mekongmind.com/docs',
      })

      await markWelcomeEmailSent(c.env.DB, tenant.id)
      return c.json({ verified: true, email_template: welcomeTemplate, message: 'Email verified. Welcome aboard!' })
    }

    return c.json({ verified: true, message: 'Email verified successfully' })
  }))
}
