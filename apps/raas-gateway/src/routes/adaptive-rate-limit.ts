/**
 * Adaptive Rate Limit routes — tenant quota management + admin controls
 *
 * Tenant (auth):
 *   GET  /adaptive-rate-limit/config      — list tenant configs
 *   POST /adaptive-rate-limit/config      — set tenant config
 *   GET  /adaptive-rate-limit/violations  — violation history
 *   GET  /adaptive-rate-limit/status      — current rate limit status
 *
 * Admin (X-Admin-Key):
 *   GET  /adaptive-rate-limit/admin/violators           — top violators
 *   POST /adaptive-rate-limit/admin/seed                — seed tier defaults
 *   POST /adaptive-rate-limit/admin/adapt/:tenantId     — adapt limits
 *   GET  /adaptive-rate-limit/admin/tier-defaults       — list tier defaults
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getTenantConfigs,
  setTenantConfig,
  getViolationHistory,
  checkRateLimit,
  getRateLimitHeaders,
  getTopViolators,
  seedTierDefaults,
  adaptLimits,
  getTierDefaults,
} from '../services/adaptive-rate-limit-service';

const app = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Admin guard
// ---------------------------------------------------------------------------

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Tenant routes (auth required)
// ---------------------------------------------------------------------------

/** GET /config — list tenant rate limit configs */
app.get('/config', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const configs = await getTenantConfigs(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: configs });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /config — upsert tenant endpoint config */
app.post('/config', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }

  const endpointPattern = body.endpoint_pattern as string;
  if (!endpointPattern) {
    return json({ error: 'endpoint_pattern required', code: 'BAD_REQUEST' }, { status: 400 });
  }

  try {
    await setTenantConfig(c.env.DB, tenant.tenantId, endpointPattern, {
      requests_per_minute: body.requests_per_minute as number | undefined,
      requests_per_hour: body.requests_per_hour as number | undefined,
      burst_allowance: body.burst_allowance as number | undefined,
      throttle_strategy: body.throttle_strategy as string | undefined,
    });
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, endpoint_pattern: endpointPattern } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** GET /violations — violation history for current tenant */
app.get('/violations', auth(), async (c) => {
  const tenant = getTenant(c);
  const days = Math.min(Math.max(parseInt(c.req.query('days') ?? '7', 10), 1), 90);
  try {
    const violations = await getViolationHistory(c.env.DB, tenant.tenantId, days);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, days, violations } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** GET /status — rate limit status for current tenant */
app.get('/status', auth(), async (c) => {
  const tenant = getTenant(c);
  const endpoint = c.req.query('endpoint') ?? '*';
  try {
    const result = await checkRateLimit(c.env.DB, c.env.RATE_LIMIT_KV, tenant.tenantId, endpoint, tenant.tier);
    const headers = getRateLimitHeaders(result);
    for (const [k, v] of Object.entries(headers)) c.header(k, v);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, tier: tenant.tier, ...result } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Rate limit check failed';
    return json({ error: message, code: 'RATE_LIMIT_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

/** GET /admin/violators — tenants with most violations (30d) */
app.get('/admin/violators', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '10', 10), 1), 100);
  try {
    const violators = await getTopViolators(c.env.DB, limit);
    return c.json({ success: true, data: violators });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /admin/seed — insert/replace tier defaults */
app.post('/admin/seed', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    await seedTierDefaults(c.env.DB);
    return c.json({ success: true, data: { seeded: ['starter', 'pro', 'enterprise'] } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Seed failed';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /admin/adapt/:tenantId — adapt limits based on violation history */
app.post('/admin/adapt/:tenantId', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  const tenantId = c.req.param('tenantId');
  try {
    const result = await adaptLimits(c.env.DB, tenantId);
    return c.json({ success: true, data: { tenant_id: tenantId, ...result } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Adapt failed';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** GET /admin/tier-defaults — list all tier defaults */
app.get('/admin/tier-defaults', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    const tiers = ['starter', 'pro', 'enterprise'];
    const results = await Promise.all(tiers.map(t => getTierDefaults(c.env.DB, t)));
    return c.json({ success: true, data: results.filter(Boolean) });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

export { app as adaptiveRateLimit };
