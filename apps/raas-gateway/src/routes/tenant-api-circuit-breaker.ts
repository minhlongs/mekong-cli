/**
 * Tenant API Circuit Breaker Routes
 * Per-tenant circuit breaker configs and event log.
 *
 * GET  /breakers          — list circuit breakers (auth)
 * POST /breakers          — create circuit breaker (auth)
 * GET  /events            — list breaker events (auth)
 * GET  /admin/overview    — platform-wide stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiCircuitBreakerService } from '../services/tenant-api-circuit-breaker';

// Inline Bindings type — keeps this file self-contained
type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── Tenant routes (JWT / API key auth) ────────────────────────────────────────

/**
 * GET /breakers — list all circuit breakers for the authenticated tenant
 */
app.get('/breakers', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiCircuitBreakerService.listBreakers(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to list circuit breakers' }, 500);
  }
});

/**
 * POST /breakers — create a new circuit breaker for the authenticated tenant
 * Body: { endpoint_pattern, failure_threshold?, recovery_timeout_ms? }
 */
app.post('/breakers', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      endpoint_pattern?: string;
      failure_threshold?: number;
      recovery_timeout_ms?: number;
    };

    const endpointPattern = body.endpoint_pattern?.trim();
    if (!endpointPattern) {
      return c.json({ error: 'endpoint_pattern is required' }, 400);
    }

    const result = await tenantApiCircuitBreakerService.createBreaker(c.env.DB, tenantId, {
      endpoint_pattern: endpointPattern,
      failure_threshold: body.failure_threshold,
      recovery_timeout_ms: body.recovery_timeout_ms,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create circuit breaker' }, 500);
  }
});

/**
 * GET /events — list circuit breaker events for the authenticated tenant
 * Query: limit (default 50, max 200), breaker_id (optional filter)
 */
app.get('/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const breakerId = c.req.query('breaker_id');

    const result = await tenantApiCircuitBreakerService.getEvents(c.env.DB, tenantId, {
      limit,
      breakerId: breakerId ?? undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to list circuit breaker events' }, 500);
  }
});

// ── Admin route (X-Admin-Key) ──────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide circuit breaker stats across all tenants
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await tenantApiCircuitBreakerService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiCircuitBreaker };
