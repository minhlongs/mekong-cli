/**
 * Admin analytics routes — revenue KPIs, cohort retention, conversion funnel
 * All endpoints protected by X-Admin-Key header (same as admin.ts)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

export const adminAnalytics = new Hono<{ Bindings: Env }>();

// Reuse same admin auth pattern from admin.ts
adminAnalytics.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
});

// Tier pricing map (mirrors admin.ts)
const TIER_PRICES: Record<string, number> = {
  starter: 49,
  pro: 149,
  enterprise: 499,
};

// GET /admin/analytics/revenue — MRR, ARR, active subs, churn, growth, breakdown
adminAnalytics.get('/revenue', async (c) => {
  const [tiers, totalRevenue, activeSubs, churnedThisMonth, lastMonthSubs] = await Promise.all([
    // Active tenants grouped by tier
    c.env.DB.prepare(
      `SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`
    ).all(),
    // Total credits purchased (revenue proxy)
    c.env.DB.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total FROM credit_transactions WHERE type = 'purchase'`
    ).first<{ total: number }>(),
    // Active subscriptions count
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM subscriptions WHERE status = 'active'`
    ).first<{ count: number }>(),
    // Churned (deactivated) this calendar month
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM tenants WHERE active = 0
       AND updated_at >= datetime('now', 'start of month')`
    ).first<{ count: number }>(),
    // Active tenants at start of last month (for growth rate)
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM tenants WHERE active = 1
       AND created_at < datetime('now', 'start of month')`
    ).first<{ count: number }>(),
  ]);

  // Compute MRR from active tier counts
  let mrr = 0;
  const revenueByTier = (tiers.results as any[]).map((row) => {
    const tierMrr = (TIER_PRICES[row.tier] || 0) * row.count;
    mrr += tierMrr;
    return { tier: row.tier, count: row.count, mrr: tierMrr };
  });

  const activeCount = (activeSubs?.count ?? 0);
  const churnedCount = (churnedThisMonth?.count ?? 0);
  const lastMonthCount = (lastMonthSubs?.count ?? 0);

  const churnRate = activeCount > 0
    ? Math.round((churnedCount / (activeCount + churnedCount)) * 1000) / 10
    : 0;

  const growthRate = lastMonthCount > 0
    ? Math.round(((activeCount - lastMonthCount) / lastMonthCount) * 1000) / 10
    : 0;

  return json({
    mrr,
    arr: mrr * 12,
    totalRevenue: totalRevenue?.total ?? 0,
    activeSubscriptions: activeCount,
    churnRate,
    growthRate,
    revenueByTier,
  });
});

// GET /admin/analytics/cohort — Monthly cohort retention (signup month → mission activity)
adminAnalytics.get('/cohort', async (c) => {
  // Tenants grouped by signup month with mission counts in following months
  const cohortData = await c.env.DB.prepare(
    `SELECT
       strftime('%Y-%m', t.created_at) as cohort_month,
       COUNT(DISTINCT t.id) as signups,
       COUNT(DISTINCT CASE
         WHEN julianday(m.created_at) - julianday(t.created_at) BETWEEN 0 AND 30
         THEN m.tenant_id END) as month1,
       COUNT(DISTINCT CASE
         WHEN julianday(m.created_at) - julianday(t.created_at) BETWEEN 31 AND 60
         THEN m.tenant_id END) as month2
     FROM tenants t
     LEFT JOIN missions m ON m.tenant_id = t.id
     WHERE t.created_at >= datetime('now', '-6 months')
     GROUP BY cohort_month
     ORDER BY cohort_month DESC`
  ).all();

  const cohorts = (cohortData.results as any[]).map((row) => ({
    month: row.cohort_month,
    signups: row.signups,
    retained: {
      month1: row.month1,
      month2: row.month2,
    },
  }));

  return json({ cohorts });
});

// GET /admin/analytics/funnel — Signup → activated → first mission → paying
adminAnalytics.get('/funnel', async (c) => {
  const [signups, activated, firstMission, paying] = await Promise.all([
    // All tenants ever created
    c.env.DB.prepare(`SELECT COUNT(*) as count FROM tenants`).first<{ count: number }>(),
    // Active tenants (email confirmed / not immediately deactivated)
    c.env.DB.prepare(`SELECT COUNT(*) as count FROM tenants WHERE active = 1`).first<{ count: number }>(),
    // Tenants who ran at least one mission
    c.env.DB.prepare(
      `SELECT COUNT(DISTINCT tenant_id) as count FROM missions`
    ).first<{ count: number }>(),
    // Tenants with at least one purchase transaction
    c.env.DB.prepare(
      `SELECT COUNT(DISTINCT tenant_id) as count FROM credit_transactions WHERE type = 'purchase'`
    ).first<{ count: number }>(),
  ]);

  const s = signups?.count ?? 0;
  const a = activated?.count ?? 0;
  const m = firstMission?.count ?? 0;
  const p = paying?.count ?? 0;

  return json({
    signups: s,
    activated: a,
    firstMission: m,
    paying: p,
    conversionRates: {
      signupToActivated: s > 0 ? Math.round((a / s) * 1000) / 10 : 0,
      activatedToMission: a > 0 ? Math.round((m / a) * 1000) / 10 : 0,
      missionToPaying: m > 0 ? Math.round((p / m) * 1000) / 10 : 0,
    },
  });
});
