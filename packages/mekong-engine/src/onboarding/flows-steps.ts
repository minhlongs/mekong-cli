/**
 * Onboarding Signup & Tutorial Steps Logic
 */

import type { D1Database } from '@cloudflare/workers-types'
import {
  type OnboardingState,
  type TutorialProgress,
  TUTORIAL_STEPS,
  generateVerificationCode,
} from './flows-types'

export async function initializeOnboarding(
  db: D1Database,
  tenantId: string,
  email: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const now = new Date().toISOString()
    const verificationCode = generateVerificationCode()
    const verificationCodeExpires = new Date(Date.now() + 15 * 60 * 1000).toISOString()

    await db.prepare(`
      INSERT INTO onboarding_states
        (tenant_id, email, email_verified, welcome_email_sent, onboarding_step,
         verification_code, verification_code_expires, created_at, updated_at)
      VALUES (?, ?, 0, 0, 0, ?, ?, ?)
    `).bind(tenantId, email, verificationCode, verificationCodeExpires, now).run()

    return { success: true }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to initialize onboarding' }
  }
}

export async function verifyEmail(
  db: D1Database,
  tenantId: string,
  code: string
): Promise<{ success: boolean; verified?: boolean; error?: string }> {
  try {
    const result = await db.prepare(`
      SELECT verification_code, verification_code_expires, email_verified
      FROM onboarding_states WHERE tenant_id = ?
    `).bind(tenantId).first<{ verification_code: string; verification_code_expires: string; email_verified: number }>()

    if (!result) return { success: false, error: 'Onboarding state not found' }
    if (result.email_verified === 1) return { success: true, verified: true }
    if (result.verification_code !== code) return { success: false, error: 'Invalid verification code' }

    const now = new Date()
    if (now > new Date(result.verification_code_expires)) {
      return { success: false, error: 'Verification code expired' }
    }

    await db.prepare(`
      UPDATE onboarding_states
      SET email_verified = 1, verification_code = NULL, verification_code_expires = NULL, updated_at = ?
      WHERE tenant_id = ?
    `).bind(now.toISOString(), tenantId).run()

    return { success: true, verified: true }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Verification failed' }
  }
}

export async function markWelcomeEmailSent(db: D1Database, tenantId: string): Promise<void> {
  await db.prepare(`
    UPDATE onboarding_states SET welcome_email_sent = 1, updated_at = datetime('now') WHERE tenant_id = ?
  `).bind(tenantId).run()
}

export async function getOnboardingState(
  db: D1Database,
  tenantId: string
): Promise<OnboardingState | null> {
  const result = await db.prepare(`
    SELECT tenant_id,
           CAST(email_verified AS INTEGER) as email_verified,
           CAST(welcome_email_sent AS INTEGER) as welcome_email_sent,
           onboarding_step,
           CAST(onboarding_completed AS INTEGER) as onboarding_completed,
           CAST(first_command_run AS INTEGER) as first_command_run,
           tutorial_step,
           CAST(tutorial_completed AS INTEGER) as tutorial_completed,
           CAST(feedback_submitted AS INTEGER) as feedback_submitted,
           nps_score, created_at, updated_at
    FROM onboarding_states WHERE tenant_id = ?
  `).bind(tenantId).first<OnboardingState>()

  return result || null
}

export async function initializeTutorial(
  db: D1Database,
  tenantId: string
): Promise<TutorialProgress> {
  const now = new Date().toISOString()
  await db.prepare(`
    UPDATE onboarding_states SET tutorial_step = 1, tutorial_completed = 0, updated_at = ? WHERE tenant_id = ?
  `).bind(now, tenantId).run()

  return {
    tenant_id: tenantId,
    current_step: 1,
    total_steps: TUTORIAL_STEPS.length,
    completed_steps: [],
    started_at: now,
    completed_at: null,
  }
}

export async function completeTutorialStep(
  db: D1Database,
  tenantId: string,
  stepId: number
): Promise<{ success: boolean; nextStep?: number; completed?: boolean; error?: string }> {
  try {
    const state = await getOnboardingState(db, tenantId)
    if (!state) return { success: false, error: 'Onboarding state not found' }
    if (stepId !== state.tutorial_step) return { success: false, error: 'Cannot complete out-of-order steps' }

    const nextStep = stepId + 1
    const isComplete = nextStep > TUTORIAL_STEPS.length

    await db.prepare(`
      UPDATE onboarding_states
      SET tutorial_step = ?, tutorial_completed = ?, updated_at = datetime('now')
      WHERE tenant_id = ?
    `).bind(isComplete ? TUTORIAL_STEPS.length : nextStep, isComplete ? 1 : 0, tenantId).run()

    if (stepId === 4) {
      await db.prepare(`
        UPDATE onboarding_states SET first_command_run = 1, updated_at = datetime('now') WHERE tenant_id = ?
      `).bind(tenantId).run()
    }

    return { success: true, nextStep: isComplete ? undefined : nextStep, completed: isComplete }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to complete step' }
  }
}

export async function getTutorialProgress(
  db: D1Database,
  tenantId: string
): Promise<TutorialProgress | null> {
  const state = await getOnboardingState(db, tenantId)
  if (!state) return null

  return {
    tenant_id: tenantId,
    current_step: state.tutorial_step,
    total_steps: TUTORIAL_STEPS.length,
    completed_steps: Array.from({ length: state.tutorial_step - 1 }, (_, i) => i + 1),
    started_at: state.created_at,
    completed_at: state.tutorial_completed ? state.updated_at : null,
  }
}
