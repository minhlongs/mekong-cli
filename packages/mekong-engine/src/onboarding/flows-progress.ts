/**
 * Onboarding Usage Milestones & Feedback Collection Logic
 */

import type { D1Database } from '@cloudflare/workers-types'
import type { UsageMilestone, FeedbackEntry } from './flows-types'

const MILESTONE_THRESHOLDS = [10, 50, 80, 100] as const

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

export async function updateUsageAndCheckMilestones(
  db: D1Database,
  tenantId: string,
  newUsage: number
): Promise<{ milestone: 10 | 50 | 80 | 100 | null; shouldSendEmail: boolean; usagePercent: number }> {
  const current = await db.prepare(`
    SELECT tier_limit, milestone_reached,
           CAST(milestone_10_sent AS INTEGER) as m10,
           CAST(milestone_50_sent AS INTEGER) as m50,
           CAST(milestone_80_sent AS INTEGER) as m80,
           CAST(milestone_100_sent AS INTEGER) as m100
    FROM usage_milestones WHERE tenant_id = ?
  `).bind(tenantId).first<{
    tier_limit: number; milestone_reached: number | null; m10: number; m50: number; m80: number; m100: number
  }>()

  if (!current) return { milestone: null, shouldSendEmail: false, usagePercent: 0 }

  const usagePercent = Math.min(100, Math.round((newUsage / current.tier_limit) * 100))
  let reachedMilestone: 10 | 50 | 80 | 100 | null = null
  for (const threshold of MILESTONE_THRESHOLDS) {
    if (usagePercent >= threshold) reachedMilestone = threshold
  }

  const milestoneFlags = { 10: current.m10, 50: current.m50, 80: current.m80, 100: current.m100 }
  const shouldSendEmail = Boolean(
    reachedMilestone && reachedMilestone !== current.milestone_reached && milestoneFlags[reachedMilestone] === 0
  )

  await db.prepare(`
    UPDATE usage_milestones
    SET current_usage = ?, milestone_reached = ?, updated_at = datetime('now')
    WHERE tenant_id = ?
  `).bind(newUsage, reachedMilestone, tenantId).run()

  return { milestone: reachedMilestone, shouldSendEmail, usagePercent }
}

export async function markMilestoneEmailSent(
  db: D1Database,
  tenantId: string,
  milestone: 10 | 50 | 80 | 100
): Promise<void> {
  const column = `milestone_${milestone}_sent`
  await db.prepare(`
    UPDATE usage_milestones SET ${column} = 1, updated_at = datetime('now') WHERE tenant_id = ?
  `).bind(tenantId).run()
}

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
    FROM usage_milestones WHERE tenant_id = ?
  `).bind(tenantId).first<UsageMilestone & { m10: number; m50: number; m80: number; m100: number }>()

  if (!result) return null

  return {
    ...result,
    usage_percent: result.usage_percent || 0,
    milestone_reached: result.milestone_reached as 10 | 50 | 80 | 100 | null,
    emails_sent: {
      milestone_10: result.m10 === 1,
      milestone_50: result.m50 === 1,
      milestone_80: result.m80 === 1,
      milestone_100: result.m100 === 1,
    },
  }
}

export async function submitNpsScore(
  db: D1Database,
  tenantId: string,
  score: number
): Promise<{ success: boolean; error?: string }> {
  if (score < 0 || score > 10) return { success: false, error: 'NPS score must be between 0 and 10' }

  try {
    const id = `fb_${tenantId}_nps_${Date.now()}`
    const now = new Date().toISOString()

    await db.prepare(`
      INSERT INTO feedback_entries (id, tenant_id, type, score, feedback, created_at)
      VALUES (?, ?, 'nps', ?, '', ?)
    `).bind(id, tenantId, score, now).run()

    await db.prepare(`
      UPDATE onboarding_states SET nps_score = ?, feedback_submitted = 1, updated_at = ? WHERE tenant_id = ?
    `).bind(score, now, tenantId).run()

    return { success: true }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Failed to submit NPS' }
  }
}

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

export async function getFeedbackEntries(db: D1Database, tenantId: string): Promise<FeedbackEntry[]> {
  const { results } = await db.prepare(`
    SELECT id, tenant_id, type, score, feedback, category, created_at
    FROM feedback_entries WHERE tenant_id = ? ORDER BY created_at DESC
  `).bind(tenantId).all<FeedbackEntry>()
  return results || []
}

export async function getAllFeedbackEntries(db: D1Database, limit = 100): Promise<FeedbackEntry[]> {
  const { results } = await db.prepare(`
    SELECT id, tenant_id, type, score, feedback, category, created_at
    FROM feedback_entries ORDER BY created_at DESC LIMIT ?
  `).bind(limit).all<FeedbackEntry>()
  return results || []
}

export async function getAverageNpsScore(
  db: D1Database,
  tenantId?: string
): Promise<{ average: number; count: number }> {
  const query = tenantId
    ? "SELECT AVG(score) as avg, COUNT(*) as count FROM feedback_entries WHERE tenant_id = ? AND type = 'nps'"
    : "SELECT AVG(score) as avg, COUNT(*) as count FROM feedback_entries WHERE type = 'nps'"

  const result = await (tenantId
    ? db.prepare(query).bind(tenantId).first<{ avg: number; count: number }>()
    : db.prepare(query).first<{ avg: number; count: number }>())

  return {
    average: result?.avg ? Math.round(result.avg * 10) / 10 : 0,
    count: result?.count || 0,
  }
}
