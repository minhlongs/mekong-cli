/**
 * Onboarding Flow Logic for Beta RaaS Gateway
 * Handles: Signup flow, First command tutorial, Usage milestones, Feedback collection
 */

import type { D1Database } from '@cloudflare/workers-types'

// ═══════════════════════════════════════════════════════════════
// TYPES & SCHEMAS
// ═══════════════════════════════════════════════════════════════

export interface OnboardingState {
  tenant_id: string
  email_verified: boolean
  welcome_email_sent: boolean
  onboarding_step: number
  onboarding_completed: boolean
  first_command_run: boolean
  tutorial_step: number
  tutorial_completed: boolean
  feedback_submitted: boolean
  nps_score: number | null
  created_at: string
  updated_at: string
}

export interface UsageMilestone {
  tenant_id: string
  tier_name: string
  tier_limit: number
  current_usage: number
  usage_percent: number
  milestone_reached: 10 | 50 | 80 | 100 | null
  emails_sent: {
    milestone_10: boolean
    milestone_50: boolean
    milestone_80: boolean
    milestone_100: boolean
  }
}

export interface FeedbackEntry {
  id: string
  tenant_id: string
  type: 'nps' | 'feature' | 'general'
  score: number | null
  feedback: string
  category?: string
  created_at: string
}

export interface TutorialProgress {
  tenant_id: string
  current_step: number
  total_steps: number
  completed_steps: number[]
  started_at: string
  completed_at: string | null
}

// ═══════════════════════════════════════════════════════════════
// SIGNUP FLOW
// ═══════════════════════════════════════════════════════════════

/**
 * Initialize onboarding state for new tenant
 */
export async function initializeOnboarding(
  db: D1Database,
  tenantId: string,
  email: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const now = new Date().toISOString()
    const verificationCode = generateVerificationCode()
    const verificationCodeExpires = new Date(Date.now() + 15 * 60 * 1000).toISOString() // 15 min

    // Insert onboarding state
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

/**
 * Verify email with code
 */
export async function verifyEmail(
  db: D1Database,
  tenantId: string,
  code: string
): Promise<{ success: boolean; verified?: boolean; error?: string }> {
  try {
    const result = await db.prepare(`
      SELECT verification_code, verification_code_expires, email_verified
      FROM onboarding_states
      WHERE tenant_id = ?
    `).bind(tenantId).first<{ verification_code: string; verification_code_expires: string; email_verified: number }>()

    if (!result) {
      return { success: false, error: 'Onboarding state not found' }
    }

    if (result.email_verified === 1) {
      return { success: true, verified: true } // Already verified
    }

    if (result.verification_code !== code) {
      return { success: false, error: 'Invalid verification code' }
    }

    const now = new Date()
    const expires = new Date(result.verification_code_expires)
    if (now > expires) {
      return { success: false, error: 'Verification code expired' }
    }

    // Mark as verified
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

/**
 * Mark welcome email as sent
 */
export async function markWelcomeEmailSent(
  db: D1Database,
  tenantId: string
): Promise<void> {
  await db.prepare(`
    UPDATE onboarding_states
    SET welcome_email_sent = 1, updated_at = datetime('now')
    WHERE tenant_id = ?
  `).bind(tenantId).run()
}

/**
 * Get onboarding state for tenant
 */
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
           nps_score,
           created_at,
           updated_at
    FROM onboarding_states
    WHERE tenant_id = ?
  `).bind(tenantId).first<OnboardingState>()

  return result || null
}

// ═══════════════════════════════════════════════════════════════
// FIRST COMMAND TUTORIAL
// ═══════════════════════════════════════════════════════════════

export const TUTORIAL_STEPS = [
  { id: 1, name: 'setup_profile', title: 'Set up your profile', description: 'Complete your business profile' },
  { id: 2, name: 'connect_channel', title: 'Connect a channel', description: 'Link your first communication channel' },
  { id: 3, name: 'explore_commands', title: 'Explore commands', description: 'Browse available commands' },
  { id: 4, name: 'run_first_command', title: 'Run your first command', description: 'Execute /cook to build something' },
  { id: 5, name: 'review_result', title: 'Review results', description: 'Check your command output' },
] as const

/**
 * Initialize tutorial for tenant
 */
export async function initializeTutorial(
  db: D1Database,
  tenantId: string
): Promise<TutorialProgress> {
  const now = new Date().toISOString()
  const progress: TutorialProgress = {
    tenant_id: tenantId,
    current_step: 1,
    total_steps: TUTORIAL_STEPS.length,
    completed_steps: [],
    started_at: now,
    completed_at: null,
  }

  // Store in onboarding state
  await db.prepare(`
    UPDATE onboarding_states
    SET tutorial_step = 1, tutorial_completed = 0, updated_at = ?
    WHERE tenant_id = ?
  `).bind(now, tenantId).run()

  return progress
}

/**
 * Mark tutorial step as completed
 */
export async function completeTutorialStep(
  db: D1Database,
  tenantId: string,
  stepId: number
): Promise<{ success: boolean; nextStep?: number; completed?: boolean; error?: string }> {
  try {
    const state = await getOnboardingState(db, tenantId)
    if (!state) {
      return { success: false, error: 'Onboarding state not found' }
    }

    if (stepId !== state.tutorial_step) {
      return { success: false, error: 'Cannot complete out-of-order steps' }
    }

    const nextStep = stepId + 1
    const isComplete = nextStep > TUTORIAL_STEPS.length

    await db.prepare(`
      UPDATE onboarding_states
      SET tutorial_step = ?,
          tutorial_completed = ?,
          updated_at = datetime('now')
      WHERE tenant_id = ?
    `).bind(isComplete ? TUTORIAL_STEPS.length : nextStep, isComplete ? 1 : 0, tenantId).run()

    // Mark first command run if completing step 4
    if (stepId === 4) {
      await db.prepare(`
        UPDATE onboarding_states
        SET first_command_run = 1, updated_at = datetime('now')
        WHERE tenant_id = ?
      `).bind(tenantId).run()
    }

    return {
      success: true,
      nextStep: isComplete ? undefined : nextStep,
      completed: isComplete,
    }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to complete step' }
  }
}

/**
 * Get tutorial progress
 */
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

// ═══════════════════════════════════════════════════════════════
// USAGE MILESTONES
// ═══════════════════════════════════════════════════════════════

const MILESTONE_THRESHOLDS = [10, 50, 80, 100] as const

/**
 * Initialize usage tracking for tenant
 */
export async function initializeUsageTracking(
  db: D1Database,
  tenantId: string,
  tierName: string,
  tierLimit: number
): Promise<void> {
  await db.prepare(`
    INSERT OR REPLACE INTO usage_milestones
      (tenant_id, tier_name, tier_limit, current_usage, milestone_reached, created_at, updated_at)
    VALUES (?, ?, ?, 0, NULL, datetime('now'), datetime('now'))
  `).bind(tenantId, tierName, tierLimit).run()
}

/**
 * Update usage and check for milestone triggers
 * Returns the milestone reached (if any) that hasn't been emailed yet
 */
export async function updateUsageAndCheckMilestones(
  db: D1Database,
  tenantId: string,
  newUsage: number
): Promise<{ milestone: 10 | 50 | 80 | 100 | null; shouldSendEmail: boolean; usagePercent: number }> {
  // Get current milestone state
  const current = await db.prepare(`
    SELECT tier_limit, milestone_reached,
           CAST(milestone_10_sent AS INTEGER) as m10,
           CAST(milestone_50_sent AS INTEGER) as m50,
           CAST(milestone_80_sent AS INTEGER) as m80,
           CAST(milestone_100_sent AS INTEGER) as m100
    FROM usage_milestones
    WHERE tenant_id = ?
  `).bind(tenantId).first<{
    tier_limit: number
    milestone_reached: number | null
    m10: number
    m50: number
    m80: number
    m100: number
  }>()

  if (!current) {
    return { milestone: null, shouldSendEmail: false, usagePercent: 0 }
  }

  const usagePercent = Math.min(100, Math.round((newUsage / current.tier_limit) * 100))

  // Determine which milestone was just reached
  let reachedMilestone: 10 | 50 | 80 | 100 | null = null
  for (const threshold of MILESTONE_THRESHOLDS) {
    if (usagePercent >= threshold) {
      reachedMilestone = threshold
    }
  }

  // Check if we should send email for this milestone
  let shouldSendEmail = false
  const milestoneFlags = {
    10: current.m10,
    50: current.m50,
    80: current.m80,
    100: current.m100,
  }

  if (reachedMilestone && reachedMilestone !== current.milestone_reached && milestoneFlags[reachedMilestone] === 0) {
    shouldSendEmail = true
  }

  // Update usage tracking
  await db.prepare(`
    UPDATE usage_milestones
    SET current_usage = ?,
        milestone_reached = ?,
        updated_at = datetime('now')
    WHERE tenant_id = ?
  `).bind(newUsage, reachedMilestone, tenantId).run()

  return { milestone: reachedMilestone, shouldSendEmail, usagePercent }
}

/**
 * Mark milestone email as sent
 */
export async function markMilestoneEmailSent(
  db: D1Database,
  tenantId: string,
  milestone: 10 | 50 | 80 | 100
): Promise<void> {
  const column = `milestone_${milestone}_sent`
  await db.prepare(`
    UPDATE usage_milestones
    SET ${column} = 1, updated_at = datetime('now')
    WHERE tenant_id = ?
  `).bind(tenantId).run()
}

/**
 * Get usage milestone status
 */
export async function getUsageMilestoneStatus(
  db: D1Database,
  tenantId: string
): Promise<UsageMilestone | null> {
  const result = await db.prepare(`
    SELECT tenant_id, tier_name, tier_limit, current_usage,
           CAST(ROUND(current_usage * 100.0 / tier_limit) AS INTEGER) as usage_percent,
           milestone_reached,
           CAST(milestone_10_sent AS INTEGER) as m10,
           CAST(milestone_50_sent AS INTEGER) as m50,
           CAST(milestone_80_sent AS INTEGER) as m80,
           CAST(milestone_100_sent AS INTEGER) as m100
    FROM usage_milestones
    WHERE tenant_id = ?
  `).bind(tenantId).first<UsageMilestone & { m10: number; m50: number; m80: number; m100: number }>()

  if (!result) return null

  return {
    ...result,
    usage_percent: result.usage_percent || 0,
    milestone_reached: result.milestone_reached as 10 | 50 | 100 | null,
    emails_sent: {
      milestone_10: result.m10 === 1,
      milestone_50: result.m50 === 1,
      milestone_80: result.m80 === 1,
      milestone_100: result.m100 === 1,
    },
  }
}

// ═══════════════════════════════════════════════════════════════
// FEEDBACK COLLECTION
// ═══════════════════════════════════════════════════════════════

/**
 * Submit NPS score
 */
export async function submitNpsScore(
  db: D1Database,
  tenantId: string,
  score: number
): Promise<{ success: boolean; error?: string }> {
  if (score < 0 || score > 10) {
    return { success: false, error: 'NPS score must be between 0 and 10' }
  }

  try {
    const id = `fb_${tenantId}_nps_${Date.now()}`
    const now = new Date().toISOString()

    await db.prepare(`
      INSERT INTO feedback_entries (id, tenant_id, type, score, feedback, created_at)
      VALUES (?, ?, 'nps', ?, '', ?)
    `).bind(id, tenantId, score, now).run()

    // Update onboarding state
    await db.prepare(`
      UPDATE onboarding_states
      SET nps_score = ?, feedback_submitted = 1, updated_at = ?
      WHERE tenant_id = ?
    `).bind(score, now, tenantId).run()

    return { success: true }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to submit NPS' }
  }
}

/**
 * Submit feature request or general feedback
 */
export async function submitFeedback(
  db: D1Database,
  tenantId: string,
  type: 'feature' | 'general',
  feedback: string,
  category?: string
): Promise<{ success: boolean; feedbackId?: string; error?: string }> {
  try {
    const id = `fb_${tenantId}_${type}_${Date.now()}`
    const now = new Date().toISOString()

    await db.prepare(`
      INSERT INTO feedback_entries (id, tenant_id, type, score, feedback, category, created_at)
      VALUES (?, ?, ?, NULL, ?, ?, ?)
    `).bind(id, tenantId, type, feedback, category || null, now).run()

    return { success: true, feedbackId: id }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to submit feedback' }
  }
}

/**
 * Get feedback entries for tenant
 */
export async function getFeedbackEntries(
  db: D1Database,
  tenantId: string
): Promise<FeedbackEntry[]> {
  const { results } = await db.prepare(`
    SELECT id, tenant_id, type, score, feedback, category, created_at
    FROM feedback_entries
    WHERE tenant_id = ?
    ORDER BY created_at DESC
  `).bind(tenantId).all<FeedbackEntry>()

  return results || []
}

/**
 * Get all feedback entries (for dashboard)
 */
export async function getAllFeedbackEntries(
  db: D1Database,
  limit = 100
): Promise<FeedbackEntry[]> {
  const { results } = await db.prepare(`
    SELECT id, tenant_id, type, score, feedback, category, created_at
    FROM feedback_entries
    ORDER BY created_at DESC
    LIMIT ?
  `).bind(limit).all<FeedbackEntry>()

  return results || []
}

/**
 * Calculate average NPS score
 */
export async function getAverageNpsScore(
  db: D1Database,
  tenantId?: string
): Promise<{ average: number; count: number }> {
  const query = tenantId
    ? 'SELECT AVG(score) as avg, COUNT(*) as count FROM feedback_entries WHERE tenant_id = ? AND type = \'nps\''
    : 'SELECT AVG(score) as avg, COUNT(*) as count FROM feedback_entries WHERE type = \'nps\''

  const result = await (tenantId
    ? db.prepare(query).bind(tenantId).first<{ avg: number; count: number }>()
    : db.prepare(query).first<{ avg: number; count: number }>()
  )

  return {
    average: result?.avg ? Math.round(result.avg * 10) / 10 : 0,
    count: result?.count || 0,
  }
}

// ═══════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════

function generateVerificationCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString()
}

export function categorizeNpsScore(score: number): 'detractor' | 'passive' | 'promoter' {
  if (score <= 6) return 'detractor'
  if (score <= 8) return 'passive'
  return 'promoter'
}
