/**
 * Admin Feature Flags routes — full CRUD + evaluation + overrides
 * All endpoints protected by X-Admin-Key header middleware
 */

import { Hono } from 'hono';
import { adminFeatureFlagsService as svc } from '../services/admin-feature-flags-service';

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

// GET /flags — paginated list with optional ?status filter
app.get('/flags', async (c) => {
  const status = c.req.query('status');
  const page = Number(c.req.query('page') ?? 1);
  const limit = Number(c.req.query('limit') ?? 20);
  const result = await svc.listFlags(c.env.DB, { status, page, limit });
  return c.json(result);
});

// POST /flags — create new flag
app.post('/flags', async (c) => {
  const body = await c.req.json();
  if (!body.flag_key || !body.name) {
    return c.json({ error: 'flag_key and name are required' }, 400);
  }
  const flag = await svc.createFlag(c.env.DB, body);
  return c.json(flag, 201);
});

// GET /flags/:id — single flag
app.get('/flags/:id', async (c) => {
  const flag = await svc.getFlag(c.env.DB, c.req.param('id'));
  if (!flag) return c.json({ error: 'Not found' }, 404);
  return c.json(flag);
});

// PUT /flags/:id — update flag
app.put('/flags/:id', async (c) => {
  const body = await c.req.json();
  const flag = await svc.updateFlag(c.env.DB, c.req.param('id'), body);
  if (!flag) return c.json({ error: 'Not found' }, 404);
  return c.json(flag);
});

// POST /flags/:id/toggle — activate or deactivate
app.post('/flags/:id/toggle', async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const status = body.status ?? 'active';
  const flag = await svc.toggleFlag(c.env.DB, c.req.param('id'), status);
  if (!flag) return c.json({ error: 'Not found' }, 404);
  return c.json(flag);
});

// DELETE /flags/:id — remove flag
app.delete('/flags/:id', async (c) => {
  const flag = await svc.getFlag(c.env.DB, c.req.param('id'));
  if (!flag) return c.json({ error: 'Not found' }, 404);
  const result = await svc.deleteFlag(c.env.DB, c.req.param('id'));
  return c.json(result);
});

// GET /evaluate/:flagKey — evaluate flag for optional tenant
app.get('/evaluate/:flagKey', async (c) => {
  const tenantId = c.req.query('tenant_id');
  const result = await svc.evaluateFlag(c.env.DB, c.req.param('flagKey'), tenantId);
  return c.json(result);
});

// GET /flags/:id/overrides — list all tenant overrides for a flag
app.get('/flags/:id/overrides', async (c) => {
  const overrides = await svc.listOverrides(c.env.DB, c.req.param('id'));
  return c.json({ overrides });
});

// POST /flags/:id/overrides — set tenant override
app.post('/flags/:id/overrides', async (c) => {
  const body = await c.req.json();
  if (!body.tenant_id || body.override_value === undefined) {
    return c.json({ error: 'tenant_id and override_value are required' }, 400);
  }
  const override = await svc.setOverride(
    c.env.DB,
    c.req.param('id'),
    body.tenant_id,
    String(body.override_value),
    body.reason,
    body.created_by
  );
  return c.json(override, 201);
});

// DELETE /flags/:id/overrides/:tenantId — remove tenant override
app.delete('/flags/:id/overrides/:tenantId', async (c) => {
  const result = await svc.removeOverride(c.env.DB, c.req.param('id'), c.req.param('tenantId'));
  return c.json(result);
});

// GET /dashboard — admin overview with flag counts and recent history
app.get('/dashboard', async (c) => {
  const overview = await svc.getAdminOverview(c.env.DB);
  return c.json(overview);
});

export { app as adminFeatureFlags };
