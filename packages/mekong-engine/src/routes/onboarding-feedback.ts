/**
 * Onboarding Tutorial, Usage & Feedback Route Handlers
 */

import type { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync } from '../types/error'
import {
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
import { createTutorialEmail, createMilestoneEmail } from '../emails/templates'
import {
  type Variables,
  tutorialStepSchema,
  npsSchema,
  feedbackSchema,
} from './onboarding-schemas'

export function registerBetaOnboardingFeedback(
  app: Hono<{ Bindings: Bindings; Variables: Variables }>
): void {
  // GET /onboarding/tutorial — get tutorial progress
  app.get('/tutorial', handleAsync(async (c) => {
    if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

    const tenant = c.get('tenant') as Tenant
    const state = await getOnboardingState(c.env.DB, tenant.id)
    if (!state) {
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
  app.post('/tutorial/step', handleAsync(async (c) => {
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
  app.get('/usage', handleAsync(async (c) => {
    if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)

    const tenant = c.get('tenant') as Tenant
    const status = await getUsageMilestoneStatus(c.env.DB, tenant.id)

    if (!status) {
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
  app.post('/usage/check', handleAsync(async (c) => {
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
  app.post('/feedback/nps', handleAsync(async (c) => {
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
}
