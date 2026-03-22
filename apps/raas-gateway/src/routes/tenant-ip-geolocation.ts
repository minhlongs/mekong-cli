/**
 * Tenant IP Geolocation routes — lookup, geo-fencing rules, access check, logs, analytics
 * Auth-protected routes use JWT/API key middleware; admin overview uses X-Admin-Key
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantIpGeolocationService as svc } from '../services/tenant-ip-geolocation-service';

type Bindings = {
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

const app = new Hono<{ Bindings: Bindings }>();

// GET /lookup/:ip — resolve geolocation for an IP address (auth)
app.get('/lookup/:ip', auth(), async (c) => {
  const ip = c.req.param('ip');
  if (!ip) return c.json({ error: 'ip is required' }, 400);
  try {
    const result = await svc.lookupIp(c.env.DB, ip);
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /rules — list tenant geo-fencing rules (auth)
app.get('/rules', auth(), async (c) => {
  const tenant = getTenant(c);
  const result = await svc.listGeoRules(c.env.DB, tenant.tenantId);
  return c.json(result);
});

// POST /rules — create a geo-fencing rule (auth)
app.post('/rules', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  try {
    const rule = await svc.createGeoRule(c.env.DB, tenant.tenantId, body);
    return c.json(rule, 201);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// PUT /rules/:id — update a geo-fencing rule (auth)
app.put('/rules/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  const body = await c.req.json().catch(() => ({}));
  const rule = await svc.updateGeoRule(c.env.DB, tenant.tenantId, id, body);
  if (!rule) return c.json({ error: 'Rule not found' }, 404);
  return c.json(rule);
});

// DELETE /rules/:id — delete a geo-fencing rule (auth)
app.delete('/rules/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  const ok = await svc.deleteGeoRule(c.env.DB, tenant.tenantId, id);
  if (!ok) return c.json({ error: 'Rule not found' }, 404);
  return c.json({ deleted: true });
});

// POST /check — check IP access against tenant geo-fencing rules (auth)
app.post('/check', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const { ip, country_code } = body;
  if (!ip || !country_code) return c.json({ error: 'ip and country_code are required' }, 400);
  try {
    const result = await svc.checkAccess(c.env.DB, tenant.tenantId, ip, country_code);
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /logs — tenant geo access logs (auth)
app.get('/logs', auth(), async (c) => {
  const tenant = getTenant(c);
  const result = await svc.getAccessLogs(c.env.DB, tenant.tenantId);
  return c.json(result);
});

// GET /analytics — tenant geo analytics (auth)
app.get('/analytics', auth(), async (c) => {
  const tenant = getTenant(c);
  const result = await svc.getGeoAnalytics(c.env.DB, tenant.tenantId);
  return c.json(result);
});

// GET /admin/overview — cross-tenant overview (admin key)
app.get('/admin/overview', async (c) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  const result = await svc.getAdminOverview(c.env.DB);
  return c.json(result);
});

export const tenantIpGeolocation = app;
