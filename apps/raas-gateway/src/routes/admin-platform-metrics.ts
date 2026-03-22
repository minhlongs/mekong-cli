/**
 * Admin Platform Metrics routes — KPI ingestion, alert rules, and dashboard
 * All endpoints: X-Admin-Key required (403 on mismatch)
 * Mount at: /admin/platform-metrics
 */

import { Hono } from 'hono';
import { adminPlatformMetricsService } from '../services/admin-platform-metrics';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  RATE_LIMIT_KV: any;
  SESSION_KV: any;
  AI: any;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — 403 on missing or wrong key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

/** GET /admin/platform-metrics/metrics — list recent metric data points
 *  Query params: metric_name (optional), limit (default 100, max 500)
 */
app.get('/metrics', async (c) => {
  try {
    const metricName = c.req.query('metric_name');
    const limit = parseInt(c.req.query('limit') ?? '100', 10) || 100;
    const result = await adminPlatformMetricsService.listMetrics(
      c.env.DB,
      metricName,
      limit
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** POST /admin/platform-metrics/metrics — record a new metric data point
 *  Body: { metric_name, metric_value, unit?, tags? }
 */
app.post('/metrics', async (c) => {
  try {
    const body = await c.req.json<{
      metric_name: string;
      metric_value: number;
      unit?: string;
      tags?: string;
    }>();

    if (!body.metric_name || body.metric_value === undefined) {
      return c.json({ error: 'metric_name and metric_value are required' }, 400);
    }

    const id = crypto.randomUUID();
    const result = await adminPlatformMetricsService.createMetric(c.env.DB, {
      id,
      metric_name: body.metric_name,
      metric_value: body.metric_value,
      unit: body.unit,
      tags: body.tags,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/platform-metrics/alerts — list alert threshold rules
 *  Query param: enabled_only=true to filter active alerts only
 */
app.get('/alerts', async (c) => {
  try {
    const enabledOnly = c.req.query('enabled_only') === 'true';
    const result = await adminPlatformMetricsService.getAlerts(
      c.env.DB,
      enabledOnly
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/platform-metrics/dashboard — latest value per metric + breached alerts */
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformMetricsService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminPlatformMetrics };
