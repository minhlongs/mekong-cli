/**
 * Tenant Health Scoring Service
 * Calculates 0-100 health score from mission success, usage trend, payments, API activity
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface HealthScore {
  score: number;
  factors: Record<string, number>;
  riskLevel: 'critical' | 'at_risk' | 'healthy' | 'excellent';
  calculatedAt: string;
}

// Scoring weights (must sum to 100)
const WEIGHTS = {
  missionSuccess: 30,
  usageTrend: 25,
  paymentHistory: 25,
  apiActivity: 20,
} as const;

export class TenantHealthService {
  /**
   * Classify risk level from numeric score
   */
  getRiskLevel(score: number): HealthScore['riskLevel'] {
    if (score < 40) return 'critical';
    if (score < 65) return 'at_risk';
    if (score < 85) return 'healthy';
    return 'excellent';
  }

  /**
   * Score mission success rate (weight 30)
   * Ratio of completed missions vs failed — no missions = neutral 50%
   */
  private async scoreMissionSuccess(db: D1Database, tenantId: string): Promise<number> {
    const row = await db
      .prepare(
        `SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
         FROM missions WHERE tenant_id = ?`
      )
      .bind(tenantId)
      .first<{ total: number; completed: number; failed: number }>();

    if (!row || row.total === 0) return 50; // neutral when no data

    const successRate = row.completed / row.total;
    return Math.round(successRate * 100);
  }

  /**
   * Score usage trend (weight 25)
   * Current month usage vs previous month — growth = high score
   */
  private async scoreUsageTrend(db: D1Database, tenantId: string): Promise<number> {
    const rows = await db
      .prepare(
        `SELECT
          SUM(CASE WHEN created_at >= datetime('now', 'start of month') THEN 1 ELSE 0 END) as current_month,
          SUM(CASE WHEN created_at >= datetime('now', 'start of month', '-1 month')
               AND created_at < datetime('now', 'start of month') THEN 1 ELSE 0 END) as prev_month
         FROM usage_records WHERE tenant_id = ?`
      )
      .bind(tenantId)
      .first<{ current_month: number; prev_month: number }>();

    const curr = rows?.current_month ?? 0;
    const prev = rows?.prev_month ?? 0;

    if (prev === 0 && curr === 0) return 50; // neutral when no history
    if (prev === 0) return 80;               // first month activity is positive

    const ratio = curr / prev;
    if (ratio >= 1.5) return 100;
    if (ratio >= 1.0) return 80;
    if (ratio >= 0.7) return 60;
    if (ratio >= 0.4) return 40;
    return 20;
  }

  /**
   * Score payment history (weight 25)
   * Fewer retries + no suspensions = high score
   */
  private async scorePaymentHistory(db: D1Database, tenantId: string): Promise<number> {
    const [retries, suspensions] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as count FROM payment_retries
           WHERE tenant_id = ? AND created_at >= datetime('now', '-90 days')`
        )
        .bind(tenantId)
        .first<{ count: number }>(),
      db
        .prepare(
          `SELECT COUNT(*) as count FROM tenant_suspensions WHERE tenant_id = ?`
        )
        .bind(tenantId)
        .first<{ count: number }>(),
    ]);

    const retryCount = retries?.count ?? 0;
    const suspensionCount = suspensions?.count ?? 0;

    if (suspensionCount > 0) return 20;
    if (retryCount === 0) return 100;
    if (retryCount <= 1) return 75;
    if (retryCount <= 3) return 50;
    return 25;
  }

  /**
   * Score API activity (weight 20)
   * Recent API calls in last 7 days — active usage = high score
   */
  private async scoreApiActivity(db: D1Database, tenantId: string): Promise<number> {
    const row = await db
      .prepare(
        `SELECT COUNT(*) as calls
         FROM usage_records
         WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
      )
      .bind(tenantId)
      .first<{ calls: number }>();

    const calls = row?.calls ?? 0;
    if (calls === 0) return 10;
    if (calls <= 5) return 40;
    if (calls <= 20) return 65;
    if (calls <= 100) return 85;
    return 100;
  }

  /**
   * Calculate composite health score and persist to DB
   */
  async calculateScore(db: D1Database, tenantId: string): Promise<HealthScore> {
    const [missionSuccess, usageTrend, paymentHistory, apiActivity] = await Promise.all([
      this.scoreMissionSuccess(db, tenantId),
      this.scoreUsageTrend(db, tenantId),
      this.scorePaymentHistory(db, tenantId),
      this.scoreApiActivity(db, tenantId),
    ]);

    const score = Math.round(
      (missionSuccess * WEIGHTS.missionSuccess +
        usageTrend * WEIGHTS.usageTrend +
        paymentHistory * WEIGHTS.paymentHistory +
        apiActivity * WEIGHTS.apiActivity) /
        100
    );

    const factors: Record<string, number> = {
      missionSuccess,
      usageTrend,
      paymentHistory,
      apiActivity,
    };

    const riskLevel = this.getRiskLevel(score);
    const calculatedAt = new Date().toISOString();

    // Persist to DB (fire-and-forget — don't block response on write errors)
    try {
      await db
        .prepare(
          `INSERT INTO tenant_health_scores (tenant_id, score, factors, risk_level, calculated_at)
           VALUES (?, ?, ?, ?, ?)`
        )
        .bind(tenantId, score, JSON.stringify(factors), riskLevel, calculatedAt)
        .run();
    } catch (err) {
      console.error('[TenantHealthService] Failed to persist health score:', err);
    }

    return { score, factors, riskLevel, calculatedAt };
  }

  /**
   * Retrieve historical health scores for a tenant
   */
  async getHistory(db: D1Database, tenantId: string, limit: number): Promise<HealthScore[]> {
    const safeLimit = Math.min(Math.max(1, limit), 100);
    const rows = await db
      .prepare(
        `SELECT score, factors, risk_level, calculated_at
         FROM tenant_health_scores
         WHERE tenant_id = ?
         ORDER BY calculated_at DESC
         LIMIT ?`
      )
      .bind(tenantId, safeLimit)
      .all<{ score: number; factors: string; risk_level: string; calculated_at: string }>();

    return (rows.results ?? []).map((r) => ({
      score: r.score,
      factors: JSON.parse(r.factors) as Record<string, number>,
      riskLevel: r.risk_level as HealthScore['riskLevel'],
      calculatedAt: r.calculated_at,
    }));
  }
}
