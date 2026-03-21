/**
 * Rate Limit V2 routes — Token Bucket + Burst + Cooldown
 *
 * Public:
 *   GET  /rate-limits/tiers         — all tier limit configs
 *
 * Tenant (auth required):
 *   GET  /rate-limits               — current rate limit status
 *   GET  /rate-limits/history       — event history (?hours=24)
 *
 * Admin (X-Admin-Key required):
 *   PUT  /rate-limits/custom        — set custom limits for a tenant
 *   GET  /rate-limits/top-limited   — most rate-limited tenants (?hours=24&limit=10)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  TIER_LIMITS,
  checkRateLimit,
  getRateLimitStatus,
  setCustomLimit,
  getCustomLimit,
  getRateLimitHistory,
  getTopRateLimitedTenants,
  type RateLimitConfig,
} from '../services/rate-limit-v2-service';

export const rateLimitV2 = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Public
// ---------------------------------------------------------------------------

/** GET /rate-limits/tiers — show all tier limit configs */
rateLimitV2.get('/tiers', (c) => {
  return c.json({ success: true, data: TIER_LIMITS });
});

// ---------------------------------------------------------------------------
// Tenant routes (auth required)
// ---------------------------------------------------------------------------

/** GET /rate-limits — current rate limit status */
rateLimitV2.get('/', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const config = await getCustomLimit(c.env.DB, tenant.tenantId, tenant.tier);
    const [result, status] = await Promise.all([
      checkRateLimit(c.env.RATE_LIMIT_KV, tenant.tenantId, tenant.tier, config),
      getRateLimitStatus(c.env.RATE_LIMIT_KV, tenant.tenantId),
    ]);

    c.header('X-RateLimit-Limit', String(result.limit));
    c.header('X-RateLimit-Remaining', String(result.remaining));
    c.header('X-RateLimit-Reset', String(result.reset_at));

    return c.json({
      success: true,
      data: {
        tier: tenant.tier,
        limits: config,
        current_usage: {
          tokens_remaining: status?.tokens ?? result.remaining,
          cooldown_until: status?.cooldown_until ?? 0,
        },
        remaining: result.remaining,
        reset_at: result.reset_at,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Rate limit check failed';
    return json({ error: message, code: 'RATE_LIMIT_ERROR' }, { status: 500 });
  }
});

/** GET /rate-limits/history — rate limit event history */
rateLimitV2.get('/history', auth(), async (c) => {
  const tenant = getTenant(c);
  const hours = Math.min(Math.max(parseInt(c.req.query('hours') ?? '24', 10), 1), 168);
  try {
    const events = await getRateLimitHistory(c.env.DB, tenant.tenantId, hours);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, hours, events } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'History fetch failed';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

/** PUT /rate-limits/custom — set custom limits for a tenant */
rateLimitV2.put('/custom', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });

  let body: { tenant_id?: string } & Partial<RateLimitConfig>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body', code: 'BAD_REQUEST' }, { status: 400 });
  }

  if (!body.tenant_id) {
    return json({ error: 'tenant_id required', code: 'BAD_REQUEST' }, { status: 400 });
  }

  try {
    await setCustomLimit(c.env.DB, body.tenant_id, {
      requests_per_minute: body.requests_per_minute,
      burst_allowance: body.burst_allowance,
      cooldown_seconds: body.cooldown_seconds,
    });
    return c.json({ success: true, data: { tenant_id: body.tenant_id, updated: true } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB update failed';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

/** GET /rate-limits/top-limited — most rate-limited tenants */
rateLimitV2.get('/top-limited', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });

  const hours = Math.min(Math.max(parseInt(c.req.query('hours') ?? '24', 10), 1), 720);
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '10', 10), 1), 100);

  try {
    const tenants = await getTopRateLimitedTenants(c.env.DB, hours, limit);
    return c.json({ success: true, data: { hours, limit, tenants } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB query failed';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});
