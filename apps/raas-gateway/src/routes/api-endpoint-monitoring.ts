/**
 * API Endpoint Monitoring routes — all endpoints require X-Admin-Key
 * POST /metrics, GET /metrics/:path, GET /stats/:path
 * GET /availability, PUT /availability/:path, GET /availability/:path/history
 * GET /alerts, POST /alerts, PUT /alerts/:id, DELETE /alerts/:id
 * GET /slow, GET /dashboard
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import {
  recordMetric,
  getMetrics,
  getEndpointStats,
  listAvailability,
  updateAvailability,
  getAvailabilityHistory,
  listAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  getSlowEndpoints,
  getAdminOverview,
} from '../services/api-endpoint-monitoring-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth middleware applied to all routes
const requireAdmin = async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
};

app.use('*', requireAdmin);

// POST /metrics — record a request metric
app.post('/metrics', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const { path, method, status_code, response_time_ms, tenant_id, error_message } = body as any;
    if (!path || !method) {
      return c.json({ error: 'path and method are required' }, 400);
    }
    await recordMetric(c.env.DB, { path, method, status_code, response_time_ms, tenant_id, error_message });
    return c.json({ ok: true }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to record metric', details: String(err) }, 500);
  }
});

// GET /metrics/:path — fetch metrics for a path (URL-encoded)
app.get('/metrics/:path', async (c) => {
  try {
    const path = decodeURIComponent(c.req.param('path'));
    const method = c.req.query('method');
    const tenant_id = c.req.query('tenant_id');
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : 100;
    const metrics = await getMetrics(c.env.DB, path, { method, tenant_id, limit });
    return c.json({ ok: true, path, count: (metrics as any[]).length, data: metrics });
  } catch (err) {
    return c.json({ error: 'Failed to fetch metrics', details: String(err) }, 500);
  }
});

// GET /stats/:path — aggregated stats for a path
app.get('/stats/:path', async (c) => {
  try {
    const path = decodeURIComponent(c.req.param('path'));
    const stats = await getEndpointStats(c.env.DB, path);
    return c.json({ ok: true, data: stats });
  } catch (err) {
    return c.json({ error: 'Failed to fetch stats', details: String(err) }, 500);
  }
});

// GET /availability — list all endpoint availability records
app.get('/availability', async (c) => {
  try {
    const data = await listAvailability(c.env.DB);
    return c.json({ ok: true, count: (data as any[]).length, data });
  } catch (err) {
    return c.json({ error: 'Failed to list availability', details: String(err) }, 500);
  }
});

// PUT /availability/:path — upsert availability for a path
app.put('/availability/:path', async (c) => {
  try {
    const path = decodeURIComponent(c.req.param('path'));
    const body = await c.req.json().catch(() => ({}));
    const { method = 'GET', status, last_check_at, uptime_pct, avg_response_ms, check_count, fail_count } = body as any;
    await updateAvailability(c.env.DB, path, method, {
      status, last_check_at, uptime_pct, avg_response_ms, check_count, fail_count,
    });
    return c.json({ ok: true, path, method });
  } catch (err) {
    return c.json({ error: 'Failed to update availability', details: String(err) }, 500);
  }
});

// GET /availability/:path/history — metric history used as availability history
app.get('/availability/:path/history', async (c) => {
  try {
    const path = decodeURIComponent(c.req.param('path'));
    const data = await getAvailabilityHistory(c.env.DB, path);
    return c.json({ ok: true, path, count: (data as any[]).length, data });
  } catch (err) {
    return c.json({ error: 'Failed to fetch availability history', details: String(err) }, 500);
  }
});

// GET /alerts — list all alert rules
app.get('/alerts', async (c) => {
  try {
    const data = await listAlerts(c.env.DB);
    return c.json({ ok: true, count: (data as any[]).length, data });
  } catch (err) {
    return c.json({ error: 'Failed to list alerts', details: String(err) }, 500);
  }
});

// POST /alerts — create alert rule
app.post('/alerts', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const { path, alert_type, condition_json, threshold, severity } = body as any;
    if (!path || !alert_type || threshold == null) {
      return c.json({ error: 'path, alert_type, and threshold are required' }, 400);
    }
    const result = await createAlert(c.env.DB, { path, alert_type, condition_json, threshold, severity });
    return c.json({ ok: true, ...result }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create alert', details: String(err) }, 500);
  }
});

// PUT /alerts/:id — update alert rule
app.put('/alerts/:id', async (c) => {
  try {
    const id = c.req.param('id');
    const body = await c.req.json().catch(() => ({}));
    const { threshold, severity, enabled, condition_json } = body as any;
    await updateAlert(c.env.DB, id, { threshold, severity, enabled, condition_json });
    return c.json({ ok: true, id });
  } catch (err) {
    return c.json({ error: 'Failed to update alert', details: String(err) }, 500);
  }
});

// DELETE /alerts/:id — delete alert rule
app.delete('/alerts/:id', async (c) => {
  try {
    const id = c.req.param('id');
    await deleteAlert(c.env.DB, id);
    return c.json({ ok: true, id });
  } catch (err) {
    return c.json({ error: 'Failed to delete alert', details: String(err) }, 500);
  }
});

// GET /slow?threshold=1000 — slow endpoints above threshold ms
app.get('/slow', async (c) => {
  try {
    const threshold = Number(c.req.query('threshold') ?? 1000);
    const data = await getSlowEndpoints(c.env.DB, threshold);
    return c.json({ ok: true, threshold_ms: threshold, count: (data as any[]).length, data });
  } catch (err) {
    return c.json({ error: 'Failed to fetch slow endpoints', details: String(err) }, 500);
  }
});

// GET /dashboard — admin overview summary
app.get('/dashboard', async (c) => {
  try {
    const data = await getAdminOverview(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to fetch dashboard', details: String(err) }, 500);
  }
});

export { app as apiEndpointMonitoring };
