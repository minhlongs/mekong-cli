/**
 * Platform KPI routes — admin-only dashboard endpoints at /admin/kpis
 * All routes require X-Admin-Key header authentication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  getMRR, getARR, getTenantMetrics, getRevenueMetrics,
  getMissionMetrics, getChurnRate, calculateLTV,
  getTopTenants, takeSnapshot, getSnapshotHistory,
} from '../services/platform-kpi-service';

export const platformKpis = new Hono<{ Bindings: Env }>();

// Admin auth guard — all routes require X-Admin-Key
platformKpis.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Unauthorized' }, 401);
  await next();
});

// GET /admin/kpis/overview — MRR, ARR, tenant + mission summary
platformKpis.get('/overview', async (c) => {
  try {
    const [mrr, arr, tenants, missions] = await Promise.all([
      getMRR(c.env.DB),
      getARR(c.env.DB),
      getTenantMetrics(c.env.DB),
      getMissionMetrics(c.env.DB),
    ]);
    return json({ mrr, arr, tenants, missions });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/revenue?period=day|week|month — revenue breakdown
platformKpis.get('/revenue', async (c) => {
  try {
    const period = c.req.query('period');
    const data = await getRevenueMetrics(c.env.DB, period);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/tenants — tenant count metrics
platformKpis.get('/tenants', async (c) => {
  try {
    const data = await getTenantMetrics(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/missions — mission throughput metrics
platformKpis.get('/missions', async (c) => {
  try {
    const data = await getMissionMetrics(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/churn — churn rate and at-risk tenant count
platformKpis.get('/churn', async (c) => {
  try {
    const data = await getChurnRate(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/top-tenants?limit=10 — top tenants by revenue
platformKpis.get('/top-tenants', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') ?? '10', 10);
    const data = await getTopTenants(c.env.DB, Math.min(limit, 100));
    return json({ tenants: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/ltv/:tenantId — lifetime value for a specific tenant
platformKpis.get('/ltv/:tenantId', async (c) => {
  try {
    const { tenantId } = c.req.param();
    const data = await calculateLTV(c.env.DB, tenantId);
    if (!data) return json({ error: 'Tenant not found' }, { status: 404 });
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /admin/kpis/snapshot — create/update daily KPI snapshot
platformKpis.post('/snapshot', async (c) => {
  try {
    const result = await takeSnapshot(c.env.DB);
    return json({ success: true, ...result });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/kpis/history?days=30 — historical snapshots
platformKpis.get('/history', async (c) => {
  try {
    const days = parseInt(c.req.query('days') ?? '30', 10);
    const snapshots = await getSnapshotHistory(c.env.DB, Math.min(days, 365));
    return json({ snapshots });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});
