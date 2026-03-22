/**
 * Tenant Custom Metrics routes
 * Mount at: /v1/custom-metrics
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantCustomMetricsService as svc } from '../services/tenant-custom-metrics-service';
import type { Env } from '../index';

const app = new Hono<{ Bindings: Env }>();

/** GET /metrics — list all metric definitions for tenant */
app.get('/metrics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listMetrics(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-metrics GET /metrics]', err);
    return c.json({ success: false, error: 'Failed to list metrics' }, 500);
  }
});

/** POST /metrics — create a new metric definition */
app.post('/metrics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.metric_name) {
      return c.json({ success: false, error: 'metric_name is required' }, 400);
    }
    const data = await svc.createMetric(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[custom-metrics POST /metrics]', err);
    return c.json({ success: false, error: 'Failed to create metric' }, 500);
  }
});

/** GET /data-points — query data points (?metric_id=&from=&to=&limit=) */
app.get('/data-points', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const metricId = c.req.query('metric_id');
    if (!metricId) {
      return c.json({ success: false, error: 'metric_id query param required' }, 400);
    }
    const opts = {
      from: c.req.query('from'),
      to: c.req.query('to'),
      limit: c.req.query('limit') ? Number(c.req.query('limit')) : undefined,
    };
    const data = await svc.getDataPoints(c.env.DB, tenantId, metricId, opts);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-metrics GET /data-points]', err);
    return c.json({ success: false, error: 'Failed to get data points' }, 500);
  }
});

/** GET /admin/overview — platform-wide stats (admin key required) */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-metrics GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantCustomMetrics };
