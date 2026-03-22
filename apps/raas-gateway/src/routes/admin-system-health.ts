/**
 * Admin System Health routes — metrics, component health, uptime, alert rules
 * All endpoints require X-Admin-Key header. Mount path: /admin/system-health
 */

import { Hono } from 'hono';
import { adminSystemHealthService as svc } from '../services/admin-system-health-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// --- Metrics ---

// POST /metrics — record a metric data point
app.post('/metrics', async (c) => {
  try {
    const body = await c.req.json<{
      metric_name: string;
      metric_value: number;
      unit?: string;
      component?: string;
      tags?: Record<string, unknown>;
    }>();
    if (!body.metric_name || body.metric_value === undefined) {
      return c.json({ error: 'metric_name and metric_value are required' }, 400);
    }
    const metric = await svc.recordMetric(c.env.DB, body);
    return c.json(metric, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /metrics/:name — get recent metrics by name
app.get('/metrics/:name', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') ?? '100', 10);
    const metrics = await svc.getMetrics(c.env.DB, c.req.param('name'), limit);
    return c.json({ metrics, count: metrics.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Component Health ---

// GET /components — list all components
app.get('/components', async (c) => {
  try {
    const components = await svc.listComponents(c.env.DB);
    return c.json({ components, count: components.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /components/:name — upsert component health
app.put('/components/:name', async (c) => {
  try {
    const body = await c.req.json<{
      status?: string;
      last_check_at?: string;
      response_time_ms?: number;
      error_message?: string;
      metadata?: Record<string, unknown>;
    }>();
    const component = await svc.updateComponent(c.env.DB, c.req.param('name'), body);
    return c.json(component);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Uptime ---

// GET /uptime/:component — uptime history for a component
app.get('/uptime/:component', async (c) => {
  try {
    const records = await svc.getUptimeHistory(c.env.DB, c.req.param('component'));
    return c.json({ records, count: records.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Alert Rules ---

// GET /alerts — list all alert rules
app.get('/alerts', async (c) => {
  try {
    const rules = await svc.listAlertRules(c.env.DB);
    return c.json({ rules, count: rules.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /alerts — create alert rule
app.post('/alerts', async (c) => {
  try {
    const body = await c.req.json<{
      name: string;
      metric_name: string;
      condition: string;
      threshold: number;
      severity?: string;
      enabled?: boolean;
    }>();
    if (!body.name || !body.metric_name || !body.condition || body.threshold === undefined) {
      return c.json({ error: 'name, metric_name, condition, threshold are required' }, 400);
    }
    const rule = await svc.createAlertRule(c.env.DB, body);
    return c.json(rule, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /alerts/:id — update alert rule
app.put('/alerts/:id', async (c) => {
  try {
    const body = await c.req.json<{
      name?: string;
      condition?: string;
      threshold?: number;
      severity?: string;
      enabled?: boolean;
    }>();
    const rule = await svc.updateAlertRule(c.env.DB, c.req.param('id'), body);
    if (!rule) return c.json({ error: 'Alert rule not found' }, 404);
    return c.json(rule);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// DELETE /alerts/:id — delete alert rule
app.delete('/alerts/:id', async (c) => {
  try {
    const deleted = await svc.deleteAlertRule(c.env.DB, c.req.param('id'));
    if (!deleted) return c.json({ error: 'Alert rule not found' }, 404);
    return c.json({ deleted: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Actions ---

// POST /check-alerts — run alert rule checks against latest metrics
app.post('/check-alerts', async (c) => {
  try {
    const triggered = await svc.checkAlerts(c.env.DB);
    return c.json({ triggered, count: triggered.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregated system health overview
app.get('/dashboard', async (c) => {
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminSystemHealth };
