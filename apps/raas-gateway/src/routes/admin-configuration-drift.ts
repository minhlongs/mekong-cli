/**
 * Admin Configuration Drift routes — detect and track config drift between expected and actual state
 * All endpoints require X-Admin-Key header. Mount path: /admin/configuration-drift
 */

import { Hono } from 'hono';
import { adminConfigurationDriftService as svc } from '../services/admin-configuration-drift';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /detections — list drift detections, optional ?resource_type=&severity=&limit=
app.get('/detections', async (c) => {
  try {
    const resource_type = c.req.query('resource_type');
    const severity = c.req.query('severity');
    const limit = c.req.query('limit') ? parseInt(c.req.query('limit')!, 10) : 100;
    const result = await svc.listDetections(c.env.DB, { resource_type, severity, limit });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ detections: result.data, count: (result.data as unknown[]).length });
  } catch {
    return c.json({ error: 'Failed to list detections' }, 500);
  }
});

// POST /detections — record a new drift detection
app.post('/detections', async (c) => {
  try {
    const body = await c.req.json<{
      resource_type: string;
      resource_id: string;
      expected_value?: string;
      actual_value?: string;
      drift_type?: string;
      severity?: string;
    }>();
    if (!body.resource_type || !body.resource_id) {
      return c.json({ error: 'resource_type and resource_id are required' }, 400);
    }
    const result = await svc.createDetection(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data, 201);
  } catch {
    return c.json({ error: 'Failed to create detection' }, 500);
  }
});

// GET /baselines — list config baselines, optional ?resource_type=&resource_id=&limit=
app.get('/baselines', async (c) => {
  try {
    const resource_type = c.req.query('resource_type');
    const resource_id = c.req.query('resource_id');
    const limit = c.req.query('limit') ? parseInt(c.req.query('limit')!, 10) : 100;
    const result = await svc.getBaselines(c.env.DB, { resource_type, resource_id, limit });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ baselines: result.data, count: (result.data as unknown[]).length });
  } catch {
    return c.json({ error: 'Failed to list baselines' }, 500);
  }
});

// GET /dashboard — aggregated drift overview: counts by severity, drift_type, recent detections
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch {
    return c.json({ error: 'Failed to load dashboard' }, 500);
  }
});

export { app as adminConfigurationDrift };
