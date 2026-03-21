/**
 * Revenue Analytics V2 Service — cohort analysis, expansion/contraction MRR, NRR
 * Depends on revenue-analytics-v2-helpers.ts for shared utilities
 */

import type { D1Database } from '@cloudflare/workers-types';
import {
  genId, priorPeriod, getSnapshotsForPeriod, getTenantSnapshot,
  estimateTenantMrr, linearSlope, TIER_PRICES,
  type MrrBreakdown,
} from './revenue-analytics-v2-helpers';

// ─── Snapshot ──────────────────────────────────────────────────────────────

/** Record current MRR/ARR/usage snapshot for a tenant in a given period */
export async function takeRevenueSnapshot(
  db: D1Database, tenantId: string, period: string
): Promise<{ id: string }> {
  const { mrr, tier } = await estimateTenantMrr(db, tenantId);
  const credits = await db
    .prepare(`SELECT COALESCE(SUM(amount),0) as p, COALESCE(SUM(CASE WHEN amount<0 THEN ABS(amount) ELSE 0 END),0) as u
              FROM credit_transactions WHERE tenant_id = ? AND strftime('%Y-%m', created_at) = ?`)
    .bind(tenantId, period).first<{ p: number; u: number }>();
  const id = genId();
  await db.prepare(
    `INSERT OR REPLACE INTO revenue_snapshots (id,tenant_id,period,mrr,arr,credits_purchased,credits_used,plan_tier)
     VALUES (?,?,?,?,?,?,?,?)`
  ).bind(id, tenantId, period, mrr, mrr * 12, credits?.p ?? 0, credits?.u ?? 0, tier).run();
  return { id };
}

// ─── MRR Breakdown ─────────────────────────────────────────────────────────

/** Compute new/expansion/contraction/churned/reactivation MRR vs prior period */
export async function getMrrBreakdown(db: D1Database, period: string): Promise<MrrBreakdown> {
  const prior = priorPeriod(period);
  const [current, previous] = await Promise.all([
    getSnapshotsForPeriod(db, period),
    getSnapshotsForPeriod(db, prior),
  ]);
  const prevMap = new Map(previous.map(s => [s.tenant_id, s.mrr]));
  const currMap = new Map(current.map(s => [s.tenant_id, s.mrr]));

  let new_mrr = 0, expansion_mrr = 0, contraction_mrr = 0, churned_mrr = 0, reactivation_mrr = 0;

  for (const [tid, cmrr] of currMap) {
    const pmrr = prevMap.get(tid) ?? 0;
    if (pmrr === 0 && cmrr > 0) new_mrr += cmrr;
    else if (cmrr > pmrr) expansion_mrr += cmrr - pmrr;
    else if (cmrr < pmrr && cmrr > 0) contraction_mrr += pmrr - cmrr;
    else if (pmrr === 0 && cmrr > 0) reactivation_mrr += cmrr;
  }
  for (const [tid, pmrr] of prevMap) {
    if (!currMap.has(tid) && pmrr > 0) churned_mrr += pmrr;
  }

  const starting_mrr = previous.reduce((s, r) => s + r.mrr, 0);
  const ending_mrr = current.reduce((s, r) => s + r.mrr, 0);
  const net_new_mrr = new_mrr + expansion_mrr - contraction_mrr - churned_mrr + reactivation_mrr;

  return { period, new_mrr, expansion_mrr, contraction_mrr, churned_mrr, reactivation_mrr, net_new_mrr, starting_mrr, ending_mrr };
}

// ─── NRR ───────────────────────────────────────────────────────────────────

/** Net Revenue Retention = (starting + expansion - contraction - churn) / starting * 100 */
export async function getNetRevenueRetention(db: D1Database, period: string): Promise<{ period: string; nrr: number; components: MrrBreakdown }> {
  const breakdown = await getMrrBreakdown(db, period);
  const { starting_mrr, expansion_mrr, contraction_mrr, churned_mrr } = breakdown;
  const nrr = starting_mrr > 0
    ? ((starting_mrr + expansion_mrr - contraction_mrr - churned_mrr) / starting_mrr) * 100
    : 0;
  return { period, nrr: Math.round(nrr * 100) / 100, components: breakdown };
}

// ─── Cohort Analysis ───────────────────────────────────────────────────────

/** Retention matrix: for each cohort month, active counts at month+0, +1, +2... */
export async function getCohortAnalysis(db: D1Database, months: number = 6): Promise<Record<string, number[]>> {
  const cohorts = await db
    .prepare(`SELECT DISTINCT cohort_month FROM cohort_assignments ORDER BY cohort_month DESC LIMIT ?`)
    .bind(months).all<{ cohort_month: string }>();

  const result: Record<string, number[]> = {};
  for (const { cohort_month } of cohorts.results) {
    const counts: number[] = [];
    for (let offset = 0; offset < months; offset++) {
      const [cy, cm] = cohort_month.split('-').map(Number);
      const d = new Date(cy, cm - 1 + offset, 1);
      const targetPeriod = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const row = await db
        .prepare(`SELECT COUNT(DISTINCT rs.tenant_id) as cnt
                  FROM revenue_snapshots rs
                  JOIN cohort_assignments ca ON ca.tenant_id = rs.tenant_id
                  WHERE ca.cohort_month = ? AND rs.period = ? AND rs.mrr > 0`)
        .bind(cohort_month, targetPeriod).first<{ cnt: number }>();
      counts.push(row?.cnt ?? 0);
    }
    result[cohort_month] = counts;
  }
  return result;
}

// ─── Segmentation ──────────────────────────────────────────────────────────

/** Segment tenants: whales >$200, growth $50-200, starter <$50, free $0 */
export async function getCustomerSegmentation(db: D1Database): Promise<Record<string, number>> {
  const tiers = await db
    .prepare(`SELECT tier, COUNT(*) as cnt FROM tenants WHERE active = 1 GROUP BY tier`).all<{ tier: string; cnt: number }>();
  const segments = { whales: 0, growth: 0, starter: 0, free: 0 };
  for (const { tier, cnt } of tiers.results) {
    const price = TIER_PRICES[tier] ?? 0;
    if (price > 200) segments.whales += cnt;
    else if (price >= 50) segments.growth += cnt;
    else if (price > 0) segments.starter += cnt;
    else segments.free += cnt;
  }
  return segments;
}

// ─── Expansion / Contraction ───────────────────────────────────────────────

/** Tenants who increased MRR vs prior period */
export async function getExpansionRevenue(db: D1Database, period: string): Promise<Array<{ tenant_id: string; prev_mrr: number; curr_mrr: number; delta: number }>> {
  const prior = priorPeriod(period);
  const [current, previous] = await Promise.all([getSnapshotsForPeriod(db, period), getSnapshotsForPeriod(db, prior)]);
  const prevMap = new Map(previous.map(s => [s.tenant_id, s.mrr]));
  return current
    .filter(s => s.mrr > (prevMap.get(s.tenant_id) ?? 0))
    .map(s => ({ tenant_id: s.tenant_id, prev_mrr: prevMap.get(s.tenant_id) ?? 0, curr_mrr: s.mrr, delta: s.mrr - (prevMap.get(s.tenant_id) ?? 0) }))
    .sort((a, b) => b.delta - a.delta);
}

/** Tenants who decreased MRR vs prior period */
export async function getContractionRevenue(db: D1Database, period: string): Promise<Array<{ tenant_id: string; prev_mrr: number; curr_mrr: number; delta: number }>> {
  const prior = priorPeriod(period);
  const [current, previous] = await Promise.all([getSnapshotsForPeriod(db, period), getSnapshotsForPeriod(db, prior)]);
  const prevMap = new Map(previous.map(s => [s.tenant_id, s.mrr]));
  return current
    .filter(s => s.mrr < (prevMap.get(s.tenant_id) ?? 0) && s.mrr > 0)
    .map(s => ({ tenant_id: s.tenant_id, prev_mrr: prevMap.get(s.tenant_id) ?? 0, curr_mrr: s.mrr, delta: (prevMap.get(s.tenant_id) ?? 0) - s.mrr }))
    .sort((a, b) => b.delta - a.delta);
}

// ─── Top Tenants ───────────────────────────────────────────────────────────

/** Top tenants by lifetime revenue from cohort_assignments */
export async function getRevenuePerTenant(db: D1Database, limit: number = 20): Promise<Array<{ tenant_id: string; lifetime_revenue: number; current_plan: string | null }>> {
  const res = await db
    .prepare(`SELECT tenant_id, lifetime_revenue, current_plan FROM cohort_assignments ORDER BY lifetime_revenue DESC LIMIT ?`)
    .bind(limit).all<{ tenant_id: string; lifetime_revenue: number; current_plan: string | null }>();
  return res.results;
}

// ─── Cohort Assignment ─────────────────────────────────────────────────────

/** Assign tenant to a cohort month */
export async function assignCohort(
  db: D1Database, tenantId: string, cohortMonth: string, source?: string
): Promise<{ id: string }> {
  const id = genId();
  const { tier } = await estimateTenantMrr(db, tenantId);
  await db.prepare(
    `INSERT OR REPLACE INTO cohort_assignments (id,tenant_id,cohort_month,signup_source,current_plan)
     VALUES (?,?,?,?,?)`
  ).bind(id, tenantId, cohortMonth, source ?? null, tier).run();
  return { id };
}

// ─── Forecasting ───────────────────────────────────────────────────────────

/** Simple linear MRR projection for next N months based on recent snapshots */
export async function getRevenueForecasting(db: D1Database, months: number = 3): Promise<Array<{ period: string; projected_mrr: number }>> {
  // Aggregate total MRR per period from snapshots (last 6 months)
  const history = await db
    .prepare(`SELECT period, SUM(mrr) as total FROM revenue_snapshots GROUP BY period ORDER BY period DESC LIMIT 6`)
    .all<{ period: string; total: number }>();
  const sorted = history.results.reverse(); // oldest first
  const values = sorted.map(r => r.total);
  const slope = linearSlope(values);
  const lastMrr = values[values.length - 1] ?? 0;
  const lastPeriod = sorted[sorted.length - 1]?.period ?? '';

  const forecast: Array<{ period: string; projected_mrr: number }> = [];
  for (let i = 1; i <= months; i++) {
    const [y, m] = lastPeriod.split('-').map(Number);
    const d = new Date(y, m - 1 + i, 1);
    const period = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const projected_mrr = Math.max(0, Math.round((lastMrr + slope * i) * 100) / 100);
    forecast.push({ period, projected_mrr });
  }
  return forecast;
}
