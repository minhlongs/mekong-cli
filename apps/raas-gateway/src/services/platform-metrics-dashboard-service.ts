/**
 * Platform Metrics Dashboard Service
 * Real-time KPIs, tenant growth, revenue tracking, system health aggregation
 */

import type { D1Database } from '@cloudflare/workers-types';

const TIER_PRICES: Record<string, number> = { starter: 49, pro: 149, enterprise: 499 };

/** Record a point-in-time metric snapshot */
export async function captureMetricSnapshot(
  db: D1Database,
  metricName: string,
  value: number,
  dimension?: string
): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO platform_metric_snapshots (id, metric_name, metric_value, dimension)
     VALUES (?, ?, ?, ?)`
  ).bind(id, metricName, value, dimension ?? null).run();
  return { id };
}

/** Time series for a metric over the last N days */
export async function getMetricTimeline(
  db: D1Database,
  metricName: string,
  days = 30
): Promise<any[]> {
  const rows = await db.prepare(
    `SELECT metric_name, metric_value, dimension, snapshot_at
     FROM platform_metric_snapshots
     WHERE metric_name = ?
       AND snapshot_at >= datetime('now', ?)
     ORDER BY snapshot_at ASC`
  ).bind(metricName, `-${days} days`).all();
  return rows.results as any[];
}

/** Latest value for every distinct metric_name */
export async function getCurrentMetrics(db: D1Database): Promise<Record<string, number>> {
  const rows = await db.prepare(
    `SELECT metric_name, metric_value
     FROM platform_metric_snapshots
     WHERE snapshot_at = (
       SELECT MAX(snapshot_at) FROM platform_metric_snapshots p2
       WHERE p2.metric_name = platform_metric_snapshots.metric_name
     )
     GROUP BY metric_name`
  ).all();
  const result: Record<string, number> = {};
  for (const row of rows.results as any[]) {
    result[row.metric_name] = row.metric_value;
  }
  return result;
}

/** Aggregate dashboard: tenants, revenue, missions, health */
export async function getDashboardSummary(db: D1Database) {
  const [tenants, active, mrr, missionsToday, apiCalls] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenants`).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(DISTINCT tenant_id) as count FROM missions
       WHERE created_at >= datetime('now', '-30 days')`
    ).first<{ count: number }>(),
    _computeMRR(db),
    db.prepare(
      `SELECT COUNT(*) as count FROM missions
       WHERE created_at >= datetime('now', '-1 day')`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE created_at >= datetime('now', '-1 day')`
    ).first<{ count: number }>(),
  ]);

  const mrrVal = mrr;
  return {
    tenants: { total: tenants?.count ?? 0, active: active?.count ?? 0 },
    revenue: { mrr: mrrVal, arr: mrrVal * 12 },
    missions: { today: missionsToday?.count ?? 0 },
    apiCalls: { today: apiCalls?.count ?? 0 },
    capturedAt: new Date().toISOString(),
  };
}

/** Create a named goal tracking progress toward a metric target */
export async function createGoal(
  db: D1Database,
  name: string,
  metricName: string,
  targetValue: number,
  deadline?: string
): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO platform_goals (id, name, metric_name, target_value, deadline)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(id, name, metricName, targetValue, deadline ?? null).run();
  return { id };
}

/** List all platform goals */
export async function listGoals(db: D1Database): Promise<any[]> {
  const rows = await db.prepare(
    `SELECT * FROM platform_goals ORDER BY created_at DESC`
  ).all();
  return rows.results as any[];
}

/** Update current_value and mark achieved/missed if deadline passed */
export async function updateGoalProgress(
  db: D1Database,
  goalId: string,
  currentValue: number
): Promise<{ updated: boolean }> {
  const goal = await db.prepare(
    `SELECT * FROM platform_goals WHERE id = ?`
  ).bind(goalId).first<any>();
  if (!goal) return { updated: false };

  let status = goal.status as string;
  if (status === 'active') {
    if (currentValue >= goal.target_value) status = 'achieved';
    else if (goal.deadline && new Date(goal.deadline) < new Date()) status = 'missed';
  }

  await db.prepare(
    `UPDATE platform_goals
     SET current_value = ?, status = ?, updated_at = datetime('now')
     WHERE id = ?`
  ).bind(currentValue, status, goalId).run();
  return { updated: true };
}

/** Evaluate all active goals and update status based on current metric snapshots */
export async function checkGoalAchievements(db: D1Database): Promise<{ evaluated: number }> {
  const goals = await db.prepare(
    `SELECT * FROM platform_goals WHERE status = 'active'`
  ).all();
  const metrics = await getCurrentMetrics(db);
  let evaluated = 0;
  for (const goal of goals.results as any[]) {
    const current = metrics[goal.metric_name];
    if (current !== undefined) {
      await updateGoalProgress(db, goal.id, current);
      evaluated++;
    }
  }
  return { evaluated };
}

/** Tenant signup counts per day over last N days */
export async function getTenantGrowthMetrics(
  db: D1Database,
  days = 30
): Promise<any[]> {
  const rows = await db.prepare(
    `SELECT date(created_at) as date, COUNT(*) as signups
     FROM tenants
     WHERE created_at >= datetime('now', ?)
     GROUP BY date(created_at)
     ORDER BY date ASC`
  ).bind(`-${days} days`).all();
  return rows.results as any[];
}

/** MRR / ARR trends — daily revenue from credit purchases over last N days */
export async function getRevenueMetrics(
  db: D1Database,
  days = 30
): Promise<{ timeline: any[]; currentMRR: number; currentARR: number }> {
  const [timeline, mrr] = await Promise.all([
    db.prepare(
      `SELECT date(created_at) as date, COALESCE(SUM(amount), 0) as revenue
       FROM credit_transactions
       WHERE type = 'purchase'
         AND created_at >= datetime('now', ?)
       GROUP BY date(created_at)
       ORDER BY date ASC`
    ).bind(`-${days} days`).all(),
    _computeMRR(db),
  ]);
  return {
    timeline: timeline.results as any[],
    currentMRR: mrr,
    currentARR: mrr * 12,
  };
}

// --- internal helper ---

async function _computeMRR(db: D1Database): Promise<number> {
  try {
    const subs = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM subscriptions WHERE status = 'active' GROUP BY tier`
    ).all();
    if (subs.results.length > 0) {
      return (subs.results as any[]).reduce(
        (sum, r) => sum + (TIER_PRICES[r.tier] || 0) * r.count, 0
      );
    }
    const tiers = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`
    ).all();
    return (tiers.results as any[]).reduce(
      (sum, r) => sum + (TIER_PRICES[r.tier] || 0) * r.count, 0
    );
  } catch {
    return 0;
  }
}
