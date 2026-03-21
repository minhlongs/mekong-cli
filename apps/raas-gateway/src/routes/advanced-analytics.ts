/**
 * Advanced analytics routes — cohort, retention, churn risk, LTV, revenue, heatmap
 * All endpoints protected by X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  getCohortAnalysis,
  getRetentionCurve,
  getChurnRisk,
  calculateLTV,
  getRevenueMetrics,
  getUsageHeatmap,
} from '../services/analytics-engine';

export const advancedAnalytics = new Hono<{ Bindings: Env }>();

// Admin auth middleware
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

advancedAnalytics.use('/*', adminAuth());

// GET /admin/advanced-analytics/cohorts
advancedAnalytics.get('/cohorts', async (c) => {
  const period = (c.req.query('period') as 'week' | 'month') ?? 'month';
  const count = parseInt(c.req.query('count') ?? '6', 10);
  const data = await getCohortAnalysis(c.env.DB, period, count);
  return json(data);
});

// GET /admin/advanced-analytics/retention
advancedAnalytics.get('/retention', async (c) => {
  const days = parseInt(c.req.query('days') ?? '90', 10);
  const data = await getRetentionCurve(c.env.DB, days);
  return json(data);
});

// GET /admin/advanced-analytics/churn-risk
advancedAnalytics.get('/churn-risk', async (c) => {
  const data = await getChurnRisk(c.env.DB);
  return json(data);
});

// GET /admin/advanced-analytics/ltv
advancedAnalytics.get('/ltv', async (c) => {
  const tenantId = c.req.query('tenant_id');
  const data = await calculateLTV(c.env.DB, tenantId);
  return json(data);
});

// GET /admin/advanced-analytics/revenue
advancedAnalytics.get('/revenue', async (c) => {
  const data = await getRevenueMetrics(c.env.DB);
  return json(data);
});

// GET /admin/advanced-analytics/heatmap
advancedAnalytics.get('/heatmap', async (c) => {
  const tenantId = c.req.query('tenant_id');
  const data = await getUsageHeatmap(c.env.DB, tenantId);
  return json(data);
});

// GET /admin/advanced-analytics/summary — combined dashboard
advancedAnalytics.get('/summary', async (c) => {
  const [retention, churn, revenue, heatmap] = await Promise.all([
    getRetentionCurve(c.env.DB, 30),
    getChurnRisk(c.env.DB),
    getRevenueMetrics(c.env.DB),
    getUsageHeatmap(c.env.DB),
  ]);

  // Day-7 retention as key metric
  const day7 = retention.curve.find((p) => p.day === 7)?.retained_pct ?? 0;

  // Peak usage hour
  const peakHour = heatmap.heatmap.reduce(
    (best, cur) => (cur.count > best.count ? cur : best),
    { hour: 0, count: 0 }
  );

  return json({
    revenue: {
      mrr: revenue.mrr,
      arr: revenue.arr,
      growth_rate: revenue.growth_rate,
      net_revenue_retention: revenue.net_revenue_retention,
    },
    retention: {
      day_7_pct: day7,
      curve_sample: retention.curve,
    },
    churn: {
      summary: churn.summary,
      top_at_risk: churn.at_risk.slice(0, 5),
    },
    usage: {
      peak_hour: peakHour.hour,
      peak_count: peakHour.count,
    },
  });
});
