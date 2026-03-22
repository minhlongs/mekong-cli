/**
 * Tenant SSO Providers routes
 * Mount at: /v1/sso
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantSsoProvidersService as svc } from '../services/tenant-sso-providers-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// ── Provider CRUD (tenant-scoped, auth required) ─────────────────────────────

app.get('/providers', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listProviders(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso GET /providers]', err);
    return c.json({ success: false, error: 'Failed to list providers' }, 500);
  }
});

app.post('/providers', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.provider_type || !body.name) {
      return c.json({ success: false, error: 'provider_type and name are required' }, 400);
    }
    const data = await svc.createProvider(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[sso POST /providers]', err);
    return c.json({ success: false, error: 'Failed to create provider' }, 500);
  }
});

app.get('/providers/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getProvider(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ success: false, error: 'Provider not found' }, 404);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso GET /providers/:id]', err);
    return c.json({ success: false, error: 'Failed to get provider' }, 500);
  }
});

app.put('/providers/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const data = await svc.updateProvider(c.env.DB, tenantId, c.req.param('id'), body);
    if (!data) return c.json({ success: false, error: 'Provider not found' }, 404);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso PUT /providers/:id]', err);
    return c.json({ success: false, error: 'Failed to update provider' }, 500);
  }
});

app.delete('/providers/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.deleteProvider(c.env.DB, tenantId, c.req.param('id'));
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso DELETE /providers/:id]', err);
    return c.json({ success: false, error: 'Failed to delete provider' }, 500);
  }
});

// ── Login flow ────────────────────────────────────────────────────────────────

app.post('/providers/:id/login', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const ip = c.req.header('CF-Connecting-IP') ?? c.req.header('X-Forwarded-For') ?? 'unknown';
    const userAgent = c.req.header('User-Agent') ?? 'unknown';
    const data = await svc.initiateLogin(c.env.DB, tenantId, c.req.param('id'), ip, userAgent);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso POST /providers/:id/login]', err);
    return c.json({ success: false, error: 'Failed to initiate login' }, 500);
  }
});

app.post('/login/:attemptId/complete', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.email) {
      return c.json({ success: false, error: 'email is required in userData' }, 400);
    }
    const data = await svc.completeLogin(c.env.DB, tenantId, c.req.param('attemptId'), body);
    return c.json({ success: true, data });
  } catch (err: any) {
    console.error('[sso POST /login/:attemptId/complete]', err);
    const status = err?.message === 'Login attempt not found' ? 404 : 500;
    return c.json({ success: false, error: err?.message ?? 'Failed to complete login' }, status);
  }
});

// ── Sessions ──────────────────────────────────────────────────────────────────

app.get('/sessions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listSessions(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso GET /sessions]', err);
    return c.json({ success: false, error: 'Failed to list sessions' }, 500);
  }
});

app.delete('/sessions/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.revokeSession(c.env.DB, tenantId, c.req.param('id'));
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso DELETE /sessions/:id]', err);
    return c.json({ success: false, error: 'Failed to revoke session' }, 500);
  }
});

// ── Admin overview (admin key required) ──────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Unauthorized' }, 401);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[sso GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantSsoProviders };
