/**
 * Platform Tenant Scoring Service — health, engagement, revenue, and overall score management
 * Calculates composite scores and tracks history for tenant health monitoring.
 */

import { randomUUID } from 'crypto';

/** List all current tenant scores, ordered by overall_score desc */
async function listScores(db: any): Promise<unknown[]> {
  try {
    const rows = await db
      .prepare('SELECT * FROM tenant_scores ORDER BY overall_score DESC')
      .all();
    return rows.results as unknown[];
  } catch (e: unknown) {
    throw new Error(`listScores failed: ${(e as Error).message}`);
  }
}

/**
 * Calculate and upsert a tenant score.
 * Derives health from mission success rate, engagement from mission count,
 * revenue from credit purchases, then computes weighted overall score.
 */
async function calculateScore(db: any, tenantId: string): Promise<unknown> {
  try {
    const [missionStats, creditStats] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total,
             SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
           FROM missions WHERE tenant_id = ?`
        )
        .bind(tenantId)
        .first() as Promise<{ total: number; completed: number } | null>,
      db
        .prepare(
          `SELECT COALESCE(SUM(amount), 0) as total_purchased
           FROM credit_transactions WHERE tenant_id = ? AND type = 'purchase'`
        )
        .bind(tenantId)
        .first() as Promise<{ total_purchased: number } | null>,
    ]);

    const total = missionStats?.total ?? 0;
    const completed = missionStats?.completed ?? 0;
    const purchased = creditStats?.total_purchased ?? 0;

    const healthScore = total > 0 ? Math.min((completed / total) * 100, 100) : 0;
    const engagementScore = Math.min(total * 2, 100);
    const revenueScore = Math.min(purchased / 5, 100);
    const overallScore = healthScore * 0.4 + engagementScore * 0.35 + revenueScore * 0.25;

    const tier = overallScore >= 80 ? 'premium' : overallScore >= 50 ? 'growth' : 'standard';
    const now = new Date().toISOString();
    const scoreId = randomUUID();

    // Upsert current score record
    await db
      .prepare(
        `INSERT INTO tenant_scores (id, tenant_id, health_score, engagement_score, revenue_score, overall_score, tier, last_calculated)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(tenant_id) DO UPDATE SET
           health_score = excluded.health_score,
           engagement_score = excluded.engagement_score,
           revenue_score = excluded.revenue_score,
           overall_score = excluded.overall_score,
           tier = excluded.tier,
           last_calculated = excluded.last_calculated`
      )
      .bind(scoreId, tenantId, healthScore, engagementScore, revenueScore, overallScore, tier, now)
      .run();

    // Append history snapshot
    const factors = JSON.stringify({ healthScore, engagementScore, revenueScore, missionTotal: total });
    await db
      .prepare(
        `INSERT INTO tenant_score_history (id, tenant_id, overall_score, factors_json, recorded_at)
         VALUES (?, ?, ?, ?, ?)`
      )
      .bind(randomUUID(), tenantId, overallScore, factors, now)
      .run();

    return { tenantId, healthScore, engagementScore, revenueScore, overallScore, tier, calculatedAt: now };
  } catch (e: unknown) {
    throw new Error(`calculateScore failed: ${(e as Error).message}`);
  }
}

/** Get score history for a specific tenant, most recent first */
async function getHistory(db: any, tenantId: string, limit = 50): Promise<unknown[]> {
  try {
    const rows = await db
      .prepare(
        `SELECT * FROM tenant_score_history WHERE tenant_id = ?
         ORDER BY recorded_at DESC LIMIT ?`
      )
      .bind(tenantId, Math.min(limit, 200))
      .all();
    return rows.results as unknown[];
  } catch (e: unknown) {
    throw new Error(`getHistory failed: ${(e as Error).message}`);
  }
}

/** Dashboard: aggregate stats across all tenant scores */
async function getDashboard(db: any): Promise<unknown> {
  try {
    const [totals, byTier, topScorers] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as total_tenants,
                  ROUND(AVG(overall_score), 2) as avg_score,
                  ROUND(MAX(overall_score), 2) as max_score,
                  ROUND(MIN(overall_score), 2) as min_score
           FROM tenant_scores`
        )
        .first() as Promise<unknown>,
      db
        .prepare(`SELECT tier, COUNT(*) as count FROM tenant_scores GROUP BY tier`)
        .all(),
      db
        .prepare(`SELECT tenant_id, overall_score, tier FROM tenant_scores ORDER BY overall_score DESC LIMIT 10`)
        .all(),
    ]);

    return {
      summary: totals,
      byTier: (byTier as any).results,
      topScorers: (topScorers as any).results,
    };
  } catch (e: unknown) {
    throw new Error(`getDashboard failed: ${(e as Error).message}`);
  }
}

export const platformTenantScoringService = {
  listScores,
  calculateScore,
  getHistory,
  getDashboard,
};
