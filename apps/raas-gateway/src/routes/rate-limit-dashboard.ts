/**
 * Rate Limit Dashboard routes
 *
 * Admin routes (X-Admin-Key):
 *   GET    /rate-limit-dashboard/admin/rate-limits            — list all configs
 *   GET    /rate-limit-dashboard/admin/rate-limits/violations — recent violations
 *   PUT    /rate-limit-dashboard/admin/rate-limits/:tenantId  — update tenant limits
 *   DELETE /rate-limit-dashboard/admin/rate-limits/:tenantId  — reset to default
 *
 * Tenant routes (auth middleware):
 *   GET    /rate-limit-dashboard/                             — own rate limit status
 *   GET    /rate-limit-dashboard/history                      — rate limit hit history
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const rateLimitDashboard = new Hono<{ Bindings: Env }>();

// --- helpers ---

/** Verify X-Admin-Key and return 401 if invalid */
function isAdmin(c: any): boolean {
  const key = c.req.header('X-Admin-Key');
  return Boolean(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

/** KV key for per-tenant rate limit config */
function configKey(tenantId: string): string {
  return `rl:config:${tenantId}`;
}

/** KV key for per-tenant violation log (daily bucket) */
function violationKey(tenantId: string, date: string): string {
  return `rl:violations:${tenantId}:${date}`;
}

/** Today's date string YYYY-MM-DD */
function today(): string {
  return new Date().toISOString().slice(0, 10);
}

// Default limits mirrored from rate-limit-service.ts
const DEFAULT_LIMITS: Record<string, { requestsPerMinute: number; monthlyMissions: number }> = {
  free:       { requestsPerMinute: 10,   monthlyMissions: 5 },
  starter:    { requestsPerMinute: 30,   monthlyMissions: 50 },
  pro:        { requestsPerMinute: 60,   monthlyMissions: 200 },
  agency:     { requestsPerMinute: 120,  monthlyMissions: 500 },
  master:     { requestsPerMinute: 300,  monthlyMissions: 2000 },
  enterprise: { requestsPerMinute: 1000, monthlyMissions: -1 },
};

// =============================================================================
// ADMIN ROUTES
// =============================================================================

/** GET /admin/rate-limits — list all tenant rate limit configs stored in KV */
rateLimitDashboard.get('/admin/rate-limits', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    // List all rl:config:* keys
    const list = await c.env.RATE_LIMIT_KV.list({ prefix: 'rl:config:' });
    const configs = await Promise.all(
      list.keys.map(async (k) => {
        const value = await c.env.RATE_LIMIT_KV.get(k.name, 'json');
        return { tenantId: k.name.replace('rl:config:', ''), config: value };
      }),
    );
    return c.json({ success: true, data: { configs, defaults: DEFAULT_LIMITS } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});

/** GET /admin/rate-limits/violations — recent violation entries from KV */
rateLimitDashboard.get('/admin/rate-limits/violations', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const list = await c.env.RATE_LIMIT_KV.list({ prefix: 'rl:violations:' });
    const violations = await Promise.all(
      list.keys.map(async (k) => {
        const value = await c.env.RATE_LIMIT_KV.get(k.name, 'json');
        // Key format: rl:violations:{tenantId}:{date}
        const parts = k.name.split(':');
        return { tenantId: parts[2], date: parts[3], data: value };
      }),
    );
    // Sort most recent first
    violations.sort((a, b) => (b.date ?? '').localeCompare(a.date ?? ''));
    return c.json({ success: true, data: violations });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});

/** PUT /admin/rate-limits/:tenantId — update (or create) custom limits for a tenant */
rateLimitDashboard.put('/admin/rate-limits/:tenantId', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  const tenantId = c.req.param('tenantId');

  interface UpdateBody { requestsPerMinute?: number; monthlyMissions?: number }
  let body: UpdateBody = {};
  try { body = await c.req.json<UpdateBody>(); } catch { /* empty body is fine */ }

  if (
    (body.requestsPerMinute !== undefined && typeof body.requestsPerMinute !== 'number') ||
    (body.monthlyMissions   !== undefined && typeof body.monthlyMissions   !== 'number')
  ) {
    return c.json({ success: false, error: 'requestsPerMinute and monthlyMissions must be numbers' }, 400);
  }

  try {
    // Merge with existing config if present
    const existing = (await c.env.RATE_LIMIT_KV.get(configKey(tenantId), 'json') as any) ?? {};
    const patch: Record<string, unknown> = {};
    if (body.requestsPerMinute !== undefined) patch.requestsPerMinute = body.requestsPerMinute;
    if (body.monthlyMissions   !== undefined) patch.monthlyMissions   = body.monthlyMissions;
    const updated = { ...existing, ...patch, updatedAt: new Date().toISOString() };
    await c.env.RATE_LIMIT_KV.put(configKey(tenantId), JSON.stringify(updated));
    return c.json({ success: true, data: { tenantId, config: updated } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});

/** DELETE /admin/rate-limits/:tenantId — remove custom config (revert to tier default) */
rateLimitDashboard.delete('/admin/rate-limits/:tenantId', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  const tenantId = c.req.param('tenantId');
  try {
    await c.env.RATE_LIMIT_KV.delete(configKey(tenantId));
    return c.json({ success: true, data: { tenantId, reset: true, message: 'Reverted to tier default' } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});

// =============================================================================
// TENANT ROUTES (auth middleware)
// =============================================================================

/** GET /v1/rate-limits — own rate limit status: current usage vs limits per endpoint */
rateLimitDashboard.get('/v1/rate-limits', auth(), async (c) => {
  const tenant = getTenant(c);

  try {
    // Per-endpoint windows: rl:{tenantId}:{endpoint}:{window}
    const endpoints = ['/v1/missions', '/v1/credits/balance', '/v1/usage/current', '/v1/missions/batch'];
    const window = Math.floor(Date.now() / 60000); // current minute window

    const usages = await Promise.all(
      endpoints.map(async (ep) => {
        const kvKey = `rl:${tenant.tenantId}:${ep}:${window}`;
        const raw = await c.env.RATE_LIMIT_KV.get(kvKey);
        const used = raw ? parseInt(raw, 10) : 0;
        return { endpoint: ep, used, window: `minute:${window}` };
      }),
    );

    // Custom config overrides tier default
    const customConfig = (await c.env.RATE_LIMIT_KV.get(configKey(tenant.tenantId), 'json') as any) ?? null;
    const tierDefaults = DEFAULT_LIMITS[tenant.tier] ?? DEFAULT_LIMITS.free;
    const effectiveLimits = customConfig
      ? { ...tierDefaults, ...customConfig }
      : tierDefaults;

    return c.json({
      success: true,
      data: {
        tenantId: tenant.tenantId,
        tier: tenant.tier,
        limits: effectiveLimits,
        currentUsage: usages,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});

/** GET /v1/rate-limits/history — rate limit hit history for own tenant */
rateLimitDashboard.get('/v1/rate-limits/history', auth(), async (c) => {
  const tenant = getTenant(c);
  const daysParam = c.req.query('days');
  const days = Math.min(Math.max(parseInt(daysParam ?? '7', 10), 1), 30);

  try {
    const history: { date: string; violations: unknown }[] = [];

    for (let i = 0; i < days; i++) {
      const d = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
      const data = await c.env.RATE_LIMIT_KV.get(violationKey(tenant.tenantId, d), 'json');
      history.push({ date: d, violations: data ?? [] });
    }

    return c.json({ success: true, data: { tenantId: tenant.tenantId, days, history } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'KV error';
    return c.json({ success: false, error: message }, 500);
  }
});
