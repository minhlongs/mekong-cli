/**
 * Platform Metrics Dashboard routes — admin-only endpoints at /admin/dashboard
 * All routes require X-Admin-Key header authentication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  captureMetricSnapshot,
  getMetricTimeline,
  getCurrentMetrics,
  getDashboardSummary,
  createGoal,
  listGoals,
  updateGoalProgress,
  checkGoalAchievements,
  getTenantGrowthMetrics,
  getRevenueMetrics,
} from '../services/platform-metrics-dashboard-service';

export const platformMetricsDashboard = new Hono<{ Bindings: Env }>();

// Admin auth guard — all routes require X-Admin-Key
platformMetricsDashboard.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Unauthorized' }, 401);
  await next();
});

// GET /admin/dashboard — aggregated dashboard summary
platformMetricsDashboard.get('/dashboard', async (c) => {
  try {
    const data = await getDashboardSummary(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/metrics — current value for all tracked metrics
platformMetricsDashboard.get('/metrics', async (c) => {
  try {
    const data = await getCurrentMetrics(c.env.DB);
    return json({ metrics: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/metrics/:metricName?days=30 — time series for a single metric
platformMetricsDashboard.get('/metrics/:metricName', async (c) => {
  try {
    const { metricName } = c.req.param();
    const days = Math.min(parseInt(c.req.query('days') ?? '30', 10), 365);
    const timeline = await getMetricTimeline(c.env.DB, metricName, days);
    return json({ metricName, days, timeline });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/growth?days=30 — tenant signup/growth over time
platformMetricsDashboard.get('/growth', async (c) => {
  try {
    const days = Math.min(parseInt(c.req.query('days') ?? '30', 10), 365);
    const data = await getTenantGrowthMetrics(c.env.DB, days);
    return json({ days, growth: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/revenue?days=30 — MRR/ARR trends over time
platformMetricsDashboard.get('/revenue', async (c) => {
  try {
    const days = Math.min(parseInt(c.req.query('days') ?? '30', 10), 365);
    const data = await getRevenueMetrics(c.env.DB, days);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /admin/snapshot — capture a metric snapshot
// body: { metric_name: string, value: number, dimension?: string }
platformMetricsDashboard.post('/snapshot', async (c) => {
  try {
    const body = await c.req.json<{ metric_name: string; value: number; dimension?: string }>();
    if (!body.metric_name || body.value === undefined) {
      return json({ error: 'metric_name and value are required' }, { status: 400 });
    }
    const result = await captureMetricSnapshot(c.env.DB, body.metric_name, body.value, body.dimension);
    return json({ success: true, ...result }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/goals — list all goals
platformMetricsDashboard.get('/goals', async (c) => {
  try {
    const goals = await listGoals(c.env.DB);
    return json({ goals });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /admin/goals — create a new goal
// body: { name, metric_name, target_value, deadline? }
platformMetricsDashboard.post('/goals', async (c) => {
  try {
    const body = await c.req.json<{
      name: string;
      metric_name: string;
      target_value: number;
      deadline?: string;
    }>();
    if (!body.name || !body.metric_name || body.target_value === undefined) {
      return json({ error: 'name, metric_name, and target_value are required' }, { status: 400 });
    }
    const result = await createGoal(c.env.DB, body.name, body.metric_name, body.target_value, body.deadline);
    return json({ success: true, ...result }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// PUT /admin/goals/:goalId — update goal progress
// body: { current_value: number }
platformMetricsDashboard.put('/goals/:goalId', async (c) => {
  try {
    const { goalId } = c.req.param();
    const body = await c.req.json<{ current_value: number }>();
    if (body.current_value === undefined) {
      return json({ error: 'current_value is required' }, { status: 400 });
    }
    const result = await updateGoalProgress(c.env.DB, goalId, body.current_value);
    if (!result.updated) return json({ error: 'Goal not found' }, { status: 404 });
    return json({ success: true });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /admin/goals/check — evaluate all active goals against latest snapshots
platformMetricsDashboard.post('/goals/check', async (c) => {
  try {
    const result = await checkGoalAchievements(c.env.DB);
    return json({ success: true, ...result });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});
