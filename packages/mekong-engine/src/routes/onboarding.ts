/**
 * onboarding.ts — Beta onboarding flow for RaaS Gateway
 *
 * Core Flow:
 * - GET  /status           — check current step and completion
 * - POST /profile          — step 1: business info
 * - POST /channel          — step 2: connect channel
 * - POST /menu             — step 3: upload menu + generate FAQs
 * - POST /activate         — step 4: complete onboarding
 *
 * Beta Flow:
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
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync } from '../types/error'
import {
  submitFeedback,
  getFeedbackEntries,
  getAllFeedbackEntries,
  getAverageNpsScore,
} from '../onboarding/flows'
import { type Variables, feedbackSchema } from './onboarding-schemas'
import { registerCoreOnboardingSteps } from './onboarding-steps'
import { registerBetaOnboardingStatus } from './onboarding-status'
import { registerBetaOnboardingFeedback } from './onboarding-feedback'

export const onboardingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

onboardingRoutes.use('*', async (c, next) => {
  if (c.req.path.endsWith('/signup')) {
    return next()
  }
  return authMiddleware(c, next)
})

registerCoreOnboardingSteps(onboardingRoutes)
registerBetaOnboardingStatus(onboardingRoutes)
registerBetaOnboardingFeedback(onboardingRoutes)

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
