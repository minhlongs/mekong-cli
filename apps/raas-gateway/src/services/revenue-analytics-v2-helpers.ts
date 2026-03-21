/**
 * Revenue Analytics V2 Helpers — shared math/query utilities
 * Used by revenue-analytics-v2-service.ts to stay under 200 lines
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface RevenueSnapshot {
  id: string;
  tenant_id: string;
  period: string;
  mrr: number;
  arr: number;
  credits_purchased: number;
  credits_used: number;
  plan_tier: string | null;
  created_at: string;
}

export interface CohortAssignment {
  id: string;
  tenant_id: string;
  cohort_month: string;
  signup_source: string | null;
  first_payment_at: string | null;
  current_plan: string | null;
  lifetime_revenue: number;
  created_at: string;
}

export interface MrrBreakdown {
  period: string;
  new_mrr: number;
  expansion_mrr: number;
  contraction_mrr: number;
  churned_mrr: number;
  reactivation_mrr: number;
  net_new_mrr: number;
  starting_mrr: number;
  ending_mrr: number;
}

/** Generate UUID-like ID using crypto */
export function genId(): string {
  return crypto.randomUUID();
}

/** Derive prior period string from current period (YYYY-MM) */
export function priorPeriod(period: string): string {
  const [y, m] = period.split('-').map(Number);
  const d = new Date(y, m - 2, 1); // month is 0-indexed
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/** Get all snapshots for a period */
export async function getSnapshotsForPeriod(
  db: D1Database,
  period: string
): Promise<RevenueSnapshot[]> {
  const res = await db
    .prepare(`SELECT * FROM revenue_snapshots WHERE period = ?`)
    .bind(period)
    .all();
  return (res.results as unknown[]) as RevenueSnapshot[];
}

/** Get snapshot for a specific tenant + period */
export async function getTenantSnapshot(
  db: D1Database,
  tenantId: string,
  period: string
): Promise<RevenueSnapshot | null> {
  const res = await db
    .prepare(`SELECT * FROM revenue_snapshots WHERE tenant_id = ? AND period = ?`)
    .bind(tenantId, period)
    .first<RevenueSnapshot>();
  return res ?? null;
}

/** Tier to monthly price mapping */
export const TIER_PRICES: Record<string, number> = {
  starter: 49,
  pro: 149,
  enterprise: 499,
};

/** Estimate MRR for tenant from subscriptions or tier */
export async function estimateTenantMrr(
  db: D1Database,
  tenantId: string
): Promise<{ mrr: number; tier: string | null }> {
  try {
    const sub = await db
      .prepare(`SELECT tier FROM subscriptions WHERE tenant_id = ? AND status = 'active' LIMIT 1`)
      .bind(tenantId)
      .first<{ tier: string }>();
    if (sub) {
      return { mrr: TIER_PRICES[sub.tier] ?? 0, tier: sub.tier };
    }
    const tenant = await db
      .prepare(`SELECT tier FROM tenants WHERE id = ?`)
      .bind(tenantId)
      .first<{ tier: string }>();
    if (tenant) {
      return { mrr: TIER_PRICES[tenant.tier] ?? 0, tier: tenant.tier };
    }
  } catch {
    // ignore
  }
  return { mrr: 0, tier: null };
}

/** Simple linear projection slope from array of values */
export function linearSlope(values: number[]): number {
  const n = values.length;
  if (n < 2) return 0;
  const xs = values.map((_, i) => i);
  const sumX = xs.reduce((a, b) => a + b, 0);
  const sumY = values.reduce((a, b) => a + b, 0);
  const sumXY = xs.reduce((s, x, i) => s + x * values[i], 0);
  const sumX2 = xs.reduce((s, x) => s + x * x, 0);
  return (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX) || 0;
}
