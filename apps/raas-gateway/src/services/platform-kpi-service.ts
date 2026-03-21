/**
 * Platform KPI Service — admin-only cross-tenant metrics (MRR, ARR, churn, LTV)
 */

import type { D1Database } from '@cloudflare/workers-types';

const TIER_PRICES: Record<string, number> = { starter: 49, pro: 149, enterprise: 499 };

/** MRR from active subscriptions, fallback to tenant tier estimate */
export async function getMRR(db: D1Database): Promise<number> {
  try {
    // Try subscriptions table first
    const subs = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM subscriptions WHERE status = 'active' GROUP BY tier`
    ).all();
    if (subs.results.length > 0) {
      return (subs.results as any[]).reduce(
        (sum, row) => sum + (TIER_PRICES[row.tier] || 0) * row.count, 0
      );
    }
    // Fallback: estimate from tenants.tier
    const tiers = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`
    ).all();
    return (tiers.results as any[]).reduce(
      (sum, row) => sum + (TIER_PRICES[row.tier] || 0) * row.count, 0
    );
  } catch {
    return 0;
  }
}

export async function getARR(db: D1Database): Promise<number> {
  return (await getMRR(db)) * 12;
}

/** Tenant counts: total, active (mission last 30d), new (last 30d), churned (inactive 60d) */
export async function getTenantMetrics(db: D1Database) {
  const [total, active, newTenants, churned] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenants`).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(DISTINCT tenant_id) as count FROM missions
       WHERE created_at >= datetime('now', '-30 days')`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM tenants
       WHERE created_at >= datetime('now', '-30 days')`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM tenants WHERE active = 0
       AND updated_at >= datetime('now', '-60 days')`
    ).first<{ count: number }>(),
  ]);
  return {
    total: total?.count ?? 0,
    active: active?.count ?? 0,
    new: newTenants?.count ?? 0,
    churned: churned?.count ?? 0,
  };
}

/** Revenue: total credit purchases, avg per tenant, optional period filter */
export async function getRevenueMetrics(db: D1Database, period?: string) {
  const periodFilter =
    period === 'day' ? "AND created_at >= datetime('now', '-1 day')"
    : period === 'week' ? "AND created_at >= datetime('now', '-7 days')"
    : period === 'month' ? "AND created_at >= datetime('now', '-30 days')"
    : '';

  const [revenue, tenantCount] = await Promise.all([
    db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM credit_transactions
       WHERE type = 'purchase' ${periodFilter}`
    ).first<{ total: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM tenants WHERE active = 1`).first<{ count: number }>(),
  ]);

  const total = revenue?.total ?? 0;
  const count = tenantCount?.count ?? 1;
  return { total, avgPerTenant: Math.round((total / count) * 100) / 100, period: period ?? 'all' };
}

/** Mission throughput: total, completed, failed, avg per tenant */
export async function getMissionMetrics(db: D1Database) {
  const [total, completed, failed, tenantCount] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM missions`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM missions WHERE status = 'completed'`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM missions WHERE status = 'failed'`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(DISTINCT tenant_id) as count FROM missions`).first<{ count: number }>(),
  ]);
  const t = total?.count ?? 0;
  const tc = tenantCount?.count ?? 1;
  return {
    total: t,
    completed: completed?.count ?? 0,
    failed: failed?.count ?? 0,
    avgPerTenant: Math.round((t / tc) * 10) / 10,
  };
}

/** Churn: tenants with no mission activity in last 60d vs total active */
export async function getChurnRate(db: D1Database) {
  const [atRisk, total] = await Promise.all([
    db.prepare(
      `SELECT COUNT(DISTINCT t.id) as count FROM tenants t
       WHERE t.active = 1
       AND t.id NOT IN (
         SELECT tenant_id FROM missions WHERE created_at >= datetime('now', '-60 days')
       )`
    ).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM tenants WHERE active = 1`).first<{ count: number }>(),
  ]);
  const risk = atRisk?.count ?? 0;
  const tot = total?.count ?? 1;
  return {
    atRiskCount: risk,
    totalActive: tot,
    churnRate: Math.round((risk / tot) * 1000) / 10,
  };
}

/** LTV for a single tenant — total spent, months active, avg monthly spend, churn risk */
export async function calculateLTV(db: D1Database, tenantId: string) {
  const [spent, tenant] = await Promise.all([
    db.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM credit_transactions
       WHERE tenant_id = ? AND type = 'purchase'`
    ).bind(tenantId).first<{ total: number }>(),
    db.prepare(
      `SELECT created_at, active FROM tenants WHERE id = ?`
    ).bind(tenantId).first<{ created_at: string; active: number }>(),
  ]);

  if (!tenant) return null;

  const totalSpent = spent?.total ?? 0;
  const createdAt = new Date(tenant.created_at);
  const monthsActive = Math.max(1,
    Math.floor((Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24 * 30))
  );
  const avgMonthly = Math.round((totalSpent / monthsActive) * 100) / 100;
  const churnRisk: 'low' | 'medium' | 'high' =
    !tenant.active ? 'high' : avgMonthly < 20 ? 'medium' : 'low';

  return {
    tenantId,
    lifetimeValue: totalSpent,
    monthsActive,
    totalSpent,
    avgMonthlySpend: avgMonthly,
    churnRisk,
  };
}

/** Top N tenants ranked by total credit purchase revenue */
export async function getTopTenants(db: D1Database, limit = 10) {
  const rows = await db.prepare(
    `SELECT ct.tenant_id, t.name, COALESCE(SUM(ct.amount), 0) as revenue
     FROM credit_transactions ct
     LEFT JOIN tenants t ON t.id = ct.tenant_id
     WHERE ct.type = 'purchase'
     GROUP BY ct.tenant_id
     ORDER BY revenue DESC
     LIMIT ?`
  ).bind(limit).all();
  return rows.results as any[];
}

/** Upsert today's KPI snapshot (idempotent by date) */
export async function takeSnapshot(db: D1Database) {
  const [mrr, tenantMetrics, revenueMetrics, missionMetrics] = await Promise.all([
    getMRR(db),
    getTenantMetrics(db),
    getRevenueMetrics(db),
    getMissionMetrics(db),
  ]);
  const id = crypto.randomUUID();
  const date = new Date().toISOString().split('T')[0];
  const avgRev = tenantMetrics.total > 0
    ? Math.round((revenueMetrics.total / tenantMetrics.total) * 100) / 100
    : 0;

  await db.prepare(
    `INSERT INTO kpi_snapshots
       (id, snapshot_date, mrr, arr, total_tenants, active_tenants, churned_tenants,
        new_tenants, total_missions, total_revenue, avg_revenue_per_tenant)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(snapshot_date) DO UPDATE SET
       mrr=excluded.mrr, arr=excluded.arr, total_tenants=excluded.total_tenants,
       active_tenants=excluded.active_tenants, churned_tenants=excluded.churned_tenants,
       new_tenants=excluded.new_tenants, total_missions=excluded.total_missions,
       total_revenue=excluded.total_revenue, avg_revenue_per_tenant=excluded.avg_revenue_per_tenant`
  ).bind(id, date, mrr, mrr * 12, tenantMetrics.total, tenantMetrics.active,
    tenantMetrics.churned, tenantMetrics.new, missionMetrics.total,
    revenueMetrics.total, avgRev).run();

  return { snapshotDate: date, mrr, arr: mrr * 12 };
}

/** Fetch historical KPI snapshots for the last N days */
export async function getSnapshotHistory(db: D1Database, days = 30) {
  const rows = await db.prepare(
    `SELECT * FROM kpi_snapshots
     WHERE snapshot_date >= date('now', ?)
     ORDER BY snapshot_date DESC`
  ).bind(`-${days} days`).all();
  return rows.results as any[];
}
