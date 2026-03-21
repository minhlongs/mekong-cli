/**
 * Revenue Analytics V2 Routes — admin-only endpoints for cohort, MRR, NRR analytics
 * All routes protected by X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  takeRevenueSnapshot,
  getMrrBreakdown,
  getCohortAnalysis,
  getNetRevenueRetention,
  getCustomerSegmentation,
  getExpansionRevenue,
  getContractionRevenue,
  getRevenuePerTenant,
  assignCohort,
  getRevenueForecasting,
} from '../services/revenue-analytics-v2-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard
const adminAuth = async (c: any, next: any) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
};
app.use('/*', adminAuth);

// GET /revenue-analytics-v2/mrr?period=YYYY-MM
app.get('/mrr', async (c) => {
  const period = c.req.query('period') ?? new Date().toISOString().slice(0, 7);
  try {
    const data = await getMrrBreakdown(c.env.DB, period);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/cohorts?months=6
app.get('/cohorts', async (c) => {
  const months = parseInt(c.req.query('months') ?? '6', 10);
  try {
    const data = await getCohortAnalysis(c.env.DB, months);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/nrr?period=YYYY-MM
app.get('/nrr', async (c) => {
  const period = c.req.query('period') ?? new Date().toISOString().slice(0, 7);
  try {
    const data = await getNetRevenueRetention(c.env.DB, period);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/segments
app.get('/segments', async (c) => {
  try {
    const data = await getCustomerSegmentation(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/expansion?period=YYYY-MM
app.get('/expansion', async (c) => {
  const period = c.req.query('period') ?? new Date().toISOString().slice(0, 7);
  try {
    const data = await getExpansionRevenue(c.env.DB, period);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/contraction?period=YYYY-MM
app.get('/contraction', async (c) => {
  const period = c.req.query('period') ?? new Date().toISOString().slice(0, 7);
  try {
    const data = await getContractionRevenue(c.env.DB, period);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/top-tenants?limit=20
app.get('/top-tenants', async (c) => {
  const limit = parseInt(c.req.query('limit') ?? '20', 10);
  try {
    const data = await getRevenuePerTenant(c.env.DB, limit);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /revenue-analytics-v2/forecast?months=3
app.get('/forecast', async (c) => {
  const months = parseInt(c.req.query('months') ?? '3', 10);
  try {
    const data = await getRevenueForecasting(c.env.DB, months);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /revenue-analytics-v2/snapshot — body: { tenant_id, period }
app.post('/snapshot', async (c) => {
  try {
    const body = await c.req.json<{ tenant_id: string; period?: string }>();
    if (!body.tenant_id) return c.json({ error: 'tenant_id required' }, 400);
    const period = body.period ?? new Date().toISOString().slice(0, 7);
    const result = await takeRevenueSnapshot(c.env.DB, body.tenant_id, period);
    return json({ ...result, period });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /revenue-analytics-v2/assign-cohort — body: { tenant_id, cohort_month, source? }
app.post('/assign-cohort', async (c) => {
  try {
    const body = await c.req.json<{ tenant_id: string; cohort_month: string; source?: string }>();
    if (!body.tenant_id || !body.cohort_month) {
      return c.json({ error: 'tenant_id and cohort_month required' }, 400);
    }
    const result = await assignCohort(c.env.DB, body.tenant_id, body.cohort_month, body.source);
    return json(result);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

export { app as revenueAnalyticsV2 };
