/**
 * Admin Platform Config routes — CRUD, overrides, history, rollback, dashboard
 * All endpoints protected by X-Admin-Key header middleware
 */

import { Hono } from 'hono';
import { adminPlatformConfigService as svc } from '../services/admin-platform-config-service';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

// Admin auth middleware — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /configs — list all configs with optional ?category filter
app.get('/configs', async (c) => {
  const category = c.req.query('category');
  const result = await svc.listConfigs(c.env.DB, category);
  return c.json(result);
});

// GET /configs/:key — single config by key
app.get('/configs/:key', async (c) => {
  const config = await svc.getConfig(c.env.DB, c.req.param('key'));
  if (!config) return c.json({ error: 'Not found' }, 404);
  return c.json(config);
});

// PUT /configs/:key — upsert config value
app.put('/configs/:key', async (c) => {
  const body = await c.req.json();
  if (body.value === undefined) return c.json({ error: 'value is required' }, 400);
  const config = await svc.setConfig(c.env.DB, c.req.param('key'), String(body.value), {
    changedBy: body.changed_by,
    changeReason: body.change_reason,
    valueType: body.value_type,
    description: body.description,
    category: body.category,
    isSensitive: body.is_sensitive,
  });
  return c.json(config);
});

// DELETE /configs/:key — remove config
app.delete('/configs/:key', async (c) => {
  const result = await svc.deleteConfig(c.env.DB, c.req.param('key'));
  if (!result) return c.json({ error: 'Not found' }, 404);
  return c.json(result);
});

// GET /configs/:key/effective — effective value with environment override check
app.get('/configs/:key/effective', async (c) => {
  const environment = c.req.query('environment') ?? c.env.ENVIRONMENT ?? 'production';
  const result = await svc.getEffectiveConfig(c.env.DB, c.req.param('key'), environment);
  return c.json(result);
});

// GET /configs/:key/overrides — list environment overrides for a key
app.get('/configs/:key/overrides', async (c) => {
  const result = await svc.listOverrides(c.env.DB, c.req.param('key'));
  return c.json(result);
});

// POST /configs/:key/overrides — set environment override
app.post('/configs/:key/overrides', async (c) => {
  const body = await c.req.json();
  if (!body.environment || body.value === undefined) {
    return c.json({ error: 'environment and value are required' }, 400);
  }
  const override = await svc.setOverride(
    c.env.DB,
    c.req.param('key'),
    body.environment,
    String(body.value),
    body.created_by
  );
  return c.json(override, 201);
});

// DELETE /configs/:key/overrides/:environment — remove environment override
app.delete('/configs/:key/overrides/:environment', async (c) => {
  const result = await svc.removeOverride(c.env.DB, c.req.param('key'), c.req.param('environment'));
  return c.json(result);
});

// GET /configs/:key/history — paginated change history
app.get('/configs/:key/history', async (c) => {
  const page = Number(c.req.query('page') ?? 1);
  const limit = Number(c.req.query('limit') ?? 20);
  const result = await svc.getHistory(c.env.DB, c.req.param('key'), page, limit);
  return c.json(result);
});

// POST /configs/:key/rollback — restore value from history record
app.post('/configs/:key/rollback', async (c) => {
  const body = await c.req.json();
  if (!body.history_id) return c.json({ error: 'history_id is required' }, 400);
  const config = await svc.rollbackConfig(c.env.DB, c.req.param('key'), body.history_id, body.rolled_back_by);
  if (!config) return c.json({ error: 'History entry not found or no previous value to restore' }, 404);
  return c.json(config);
});

// GET /dashboard — admin overview with config counts by category
app.get('/dashboard', async (c) => {
  const overview = await svc.getAdminOverview(c.env.DB);
  return c.json(overview);
});

export { app as adminPlatformConfig };
