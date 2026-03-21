/**
 * Tenant Lifecycle Analytics — distribution, churn analysis, auto-transitions
 * Companion to tenant-lifecycle-service.ts (core CRUD/transitions)
 */

import type { D1Database } from '@cloudflare/workers-types';
import type { LifecycleRecord } from './tenant-lifecycle-service';
import { transitionStage, getLifecycleStage } from './tenant-lifecycle-service';

/** Get tenants with risk_score above threshold, ordered by risk descending */
export async function getAtRiskTenants(
  db: D1Database,
  threshold = 70
): Promise<LifecycleRecord[]> {
  const result = await db
    .prepare(
      `SELECT * FROM tenant_lifecycle WHERE risk_score > ? ORDER BY risk_score DESC`
    )
    .bind(threshold)
    .all<LifecycleRecord>();
  return result.results;
}

/** Count of tenants per lifecycle stage */
export async function getStageDistribution(
  db: D1Database
): Promise<Record<string, number>> {
  const result = await db
    .prepare(`SELECT stage, COUNT(*) as count FROM tenant_lifecycle GROUP BY stage`)
    .all<{ stage: string; count: number }>();

  return result.results.reduce(
    (acc, row) => ({ ...acc, [row.stage]: row.count }),
    {} as Record<string, number>
  );
}

/** Recently churned tenants with the reason from their last transition */
export async function getChurnAnalysis(
  db: D1Database,
  days = 30
): Promise<{ lifecycle: LifecycleRecord; lastReason: string | null }[]> {
  const churned = await db
    .prepare(
      `SELECT tl.* FROM tenant_lifecycle tl
       WHERE tl.stage = 'churned'
         AND tl.stage_entered_at >= datetime('now', ? || ' days')
       ORDER BY tl.stage_entered_at DESC`
    )
    .bind(`-${days}`)
    .all<LifecycleRecord>();

  return Promise.all(
    churned.results.map(async (lifecycle) => {
      const last = await db
        .prepare(
          `SELECT reason FROM lifecycle_transitions
           WHERE tenant_id = ? AND to_stage = 'churned'
           ORDER BY created_at DESC LIMIT 1`
        )
        .bind(lifecycle.tenant_id)
        .first<{ reason: string | null }>();
      return { lifecycle, lastReason: last?.reason ?? null };
    })
  );
}

/**
 * Evaluate and apply automatic stage transitions for all non-churned tenants.
 *
 * Rules (checked in priority order):
 * 1. trial  + trial expired          → at_risk
 * 2. at_risk + activity in last 7d   → active
 * 3. non-trial/at_risk + inactive 30d → at_risk
 * 4. at_risk + inactive 90d          → churned
 *
 * Returns count of tenants transitioned.
 */
export async function evaluateAutoTransitions(db: D1Database): Promise<number> {
  const tenants = await db
    .prepare(`SELECT * FROM tenant_lifecycle WHERE stage NOT IN ('churned')`)
    .all<LifecycleRecord>();

  let count = 0;
  const now = Date.now();

  for (const t of tenants.results) {
    const daysSinceActivity = t.last_activity_at
      ? (now - new Date(t.last_activity_at).getTime()) / 86400_000
      : 999;

    const trialExpired =
      t.stage === 'trial' && !!t.trial_ends_at && new Date(t.trial_ends_at).getTime() < now;
    const recentActivity = daysSinceActivity < 7;
    const inactive30 = daysSinceActivity > 30;
    const inactive90 = daysSinceActivity > 90;

    let nextStage: LifecycleRecord['stage'] | null = null;
    let reason = '';

    if (trialExpired) {
      nextStage = 'at_risk';
      reason = 'Trial period expired';
    } else if (t.stage === 'at_risk' && recentActivity) {
      nextStage = 'active';
      reason = 'Recent activity detected — risk resolved';
    } else if (t.stage === 'at_risk' && inactive90) {
      nextStage = 'churned';
      reason = 'Inactive for 90+ days';
    } else if (!['trial', 'at_risk'].includes(t.stage) && inactive30) {
      nextStage = 'at_risk';
      reason = 'Inactive for 30+ days';
    }

    if (nextStage) {
      await transitionStage(db, t.tenant_id, nextStage, reason, 'system');
      count++;
    }
  }

  return count;
}
