/** Advanced Analytics Engine — cohort, retention, churn risk, LTV, revenue, heatmap */

export const TIER_PRICES: Record<string, number> = { starter: 49, pro: 149, enterprise: 499 };

export async function getCohortAnalysis(
  db: any, period: 'week' | 'month' = 'month', cohortCount = 6
): Promise<{ cohorts: Array<{ period: string; size: number; retention: number[] }> }> {
  try {
    const fmt = period === 'week' ? '%Y-W%W' : '%Y-%m';
    const offset = period === 'week' ? `-${cohortCount * 7} days` : `-${cohortCount} months`;
    const cohortRows = await db.prepare(
      `SELECT strftime('${fmt}', created_at) as cohort_period, id as tenant_id
       FROM tenants WHERE created_at >= datetime('now', '${offset}') ORDER BY created_at`
    ).all();

    const cohortMap = new Map<string, string[]>();
    for (const row of cohortRows.results as any[]) {
      if (!cohortMap.has(row.cohort_period)) cohortMap.set(row.cohort_period, []);
      cohortMap.get(row.cohort_period)!.push(row.tenant_id);
    }

    const cohorts = [];
    for (const [cohortPeriod, tenantIds] of cohortMap) {
      const size = tenantIds.length;
      const retention: number[] = [100];
      const base = period === 'week'
        ? `datetime('${cohortPeriod}', 'weekday 1')`
        : `datetime('${cohortPeriod}-01')`;

      for (let i = 1; i <= Math.min(cohortCount - 1, 5); i++) {
        const p1 = period === 'week' ? `+${i * 7} days` : `+${i} months`;
        const p2 = period === 'week' ? `+${(i + 1) * 7} days` : `+${i + 1} months`;
        const ph = tenantIds.map(() => '?').join(',');
        const r = (await db.prepare(
          `SELECT COUNT(DISTINCT tenant_id) as active FROM missions
           WHERE tenant_id IN (${ph})
             AND created_at >= datetime(${base}, '${p1}')
             AND created_at < datetime(${base}, '${p2}')`
        ).bind(...tenantIds).first()) as { active: number } | null;
        retention.push(size > 0 ? Math.round(((r?.active ?? 0) / size) * 100) : 0);
      }
      cohorts.push({ period: cohortPeriod, size, retention });
    }
    return { cohorts };
  } catch { return { cohorts: [] }; }
}

export async function getRetentionCurve(
  db: any, days = 90
): Promise<{ curve: Array<{ day: number; retained_pct: number }> }> {
  try {
    const milestones = [1, 3, 7, 14, 30, 60, 90].filter((d) => d <= days);
    const totalRow = (await db.prepare(
      `SELECT COUNT(*) as total FROM tenants WHERE active = 1`
    ).first()) as { total: number } | null;
    const total = totalRow?.total ?? 0;
    if (total === 0) return { curve: milestones.map((day) => ({ day, retained_pct: 0 })) };

    const curve = [];
    for (const day of milestones) {
      const row = (await db.prepare(
        `SELECT COUNT(DISTINCT t.id) as active FROM tenants t
         WHERE t.active = 1 AND EXISTS (
           SELECT 1 FROM missions m WHERE m.tenant_id = t.id
             AND m.created_at >= datetime('now', '-${day} days'))`
      ).first()) as { active: number } | null;
      curve.push({ day, retained_pct: Math.round(((row?.active ?? 0) / total) * 100) });
    }
    return { curve };
  } catch { return { curve: [] }; }
}

export async function getChurnRisk(db: any): Promise<{
  at_risk: Array<{ tenant_id: string; risk_score: number; factors: string[]; last_active: string | null }>;
  summary: { total_active: number; high_risk: number; medium_risk: number; low_risk: number };
}> {
  try {
    const tenants = await db.prepare(
      `SELECT t.id, t.tier, t.credits,
              MAX(m.created_at) as last_mission,
              COUNT(CASE WHEN m.created_at >= datetime('now', '-7 days') THEN 1 END) as missions_7d,
              COUNT(CASE WHEN m.created_at >= datetime('now', '-14 days')
                         AND m.created_at < datetime('now', '-7 days') THEN 1 END) as missions_prev_7d,
              MAX(ak.last_used_at) as last_api_use
       FROM tenants t
       LEFT JOIN missions m ON m.tenant_id = t.id
       LEFT JOIN api_keys ak ON ak.tenant_id = t.id
       WHERE t.active = 1 GROUP BY t.id`
    ).all();

    const at_risk: Array<{ tenant_id: string; risk_score: number; factors: string[]; last_active: string | null }> = [];
    let high_risk = 0, medium_risk = 0, low_risk = 0;

    for (const row of tenants.results as any[]) {
      let score = 0;
      const factors: string[] = [];
      const daysSince = row.last_mission
        ? Math.floor((Date.now() - new Date(row.last_mission).getTime()) / 86400000)
        : 999;

      if (daysSince > 30) { score += 50; factors.push('No missions in 30+ days'); }
      else if (daysSince > 14) { score += 30; factors.push('No missions in 14+ days'); }
      if (row.missions_prev_7d > 0 && row.missions_7d < row.missions_prev_7d) { score += 20; factors.push('Mission frequency declining'); }
      if (row.credits < (TIER_PRICES[row.tier] ?? 49) * 0.1) { score += 20; factors.push('Credit balance below 10% of tier'); }

      const apiDays = row.last_api_use
        ? Math.floor((Date.now() - new Date(row.last_api_use).getTime()) / 86400000)
        : 999;
      if (apiDays > 7) { score += 10; factors.push('No API key usage in 7 days'); }

      score = Math.min(score, 100);
      if (score >= 70) high_risk++;
      else if (score >= 40) medium_risk++;
      else low_risk++;
      if (score >= 40) at_risk.push({ tenant_id: row.id, risk_score: score, factors, last_active: row.last_mission ?? null });
    }

    at_risk.sort((a, b) => b.risk_score - a.risk_score);
    return { at_risk, summary: { total_active: tenants.results.length, high_risk, medium_risk, low_risk } };
  } catch {
    return { at_risk: [], summary: { total_active: 0, high_risk: 0, medium_risk: 0, low_risk: 0 } };
  }
}

export async function calculateLTV(
  db: any, tenantId?: string
): Promise<{ average_ltv: number; median_ltv: number; by_tier: Record<string, number> }> {
  try {
    const where = tenantId ? `AND t.id = ?` : '';
    const rows = await db.prepare(
      `SELECT t.tier, COALESCE(SUM(ct.amount), 0) as total_revenue, MIN(t.created_at) as first_purchase
       FROM tenants t
       LEFT JOIN credit_transactions ct ON ct.tenant_id = t.id AND ct.type = 'purchase'
       WHERE 1=1 ${where} GROUP BY t.id`
    ).bind(...(tenantId ? [tenantId] : [])).all();

    const ltvByTier: Record<string, number[]> = {};
    const allLtvs: number[] = [];
    for (const row of rows.results as any[]) {
      const months = row.first_purchase
        ? Math.max(1, (Date.now() - new Date(row.first_purchase).getTime()) / (30 * 86400000))
        : 1;
      const ltv = Math.round((row.total_revenue / months) / 0.02); // LTV = avg_mrr / churn_rate
      allLtvs.push(ltv);
      if (!ltvByTier[row.tier]) ltvByTier[row.tier] = [];
      ltvByTier[row.tier].push(ltv);
    }

    const avg = allLtvs.length > 0 ? Math.round(allLtvs.reduce((a, b) => a + b, 0) / allLtvs.length) : 0;
    const sorted = [...allLtvs].sort((a, b) => a - b);
    const median = sorted.length > 0 ? sorted[Math.floor(sorted.length / 2)] : 0;
    const by_tier: Record<string, number> = {};
    for (const [tier, ltvs] of Object.entries(ltvByTier)) {
      by_tier[tier] = Math.round((ltvs as number[]).reduce((a, b) => a + b, 0) / ltvs.length);
    }
    return { average_ltv: avg, median_ltv: median, by_tier };
  } catch { return { average_ltv: 0, median_ltv: 0, by_tier: {} }; }
}

export async function getRevenueMetrics(db: any): Promise<{
  mrr: number; arr: number; growth_rate: number; net_revenue_retention: number;
}> {
  try {
    const [cur, prev] = await Promise.all([
      db.prepare(`SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`).all(),
      db.prepare(`SELECT tier, COUNT(*) as count FROM tenants
                  WHERE active = 1 AND created_at < datetime('now', 'start of month') GROUP BY tier`).all(),
    ]);
    const calcMrr = (rows: any[]) => rows.reduce((s: number, r: any) => s + (TIER_PRICES[r.tier] ?? 0) * r.count, 0);
    const mrr = calcMrr(cur.results as any[]);
    const prevMrr = calcMrr(prev.results as any[]);
    return {
      mrr,
      arr: mrr * 12,
      growth_rate: prevMrr > 0 ? Math.round(((mrr - prevMrr) / prevMrr) * 1000) / 10 : 0,
      net_revenue_retention: prevMrr > 0 ? Math.round((mrr / prevMrr) * 100 * 10) / 10 : 100,
    };
  } catch { return { mrr: 0, arr: 0, growth_rate: 0, net_revenue_retention: 0 }; }
}

export async function getUsageHeatmap(
  db: any, tenantId?: string
): Promise<{ heatmap: Array<{ hour: number; count: number }> }> {
  try {
    const where = tenantId ? `WHERE tenant_id = ?` : '';
    const rows = await db.prepare(
      `SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as count
       FROM missions ${where} GROUP BY hour ORDER BY hour`
    ).bind(...(tenantId ? [tenantId] : [])).all();

    const byHour = new Map<number, number>();
    for (const row of rows.results as any[]) byHour.set(row.hour, row.count);
    return { heatmap: Array.from({ length: 24 }, (_, h) => ({ hour: h, count: byHour.get(h) ?? 0 })) };
  } catch {
    return { heatmap: Array.from({ length: 24 }, (_, h) => ({ hour: h, count: 0 })) };
  }
}
