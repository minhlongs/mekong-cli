/**
 * Tenant API Throttling Routes
 * Per-tenant concurrent-request throttle rules and event log.
 *
 * GET  /rules           — list throttle rules (auth)
 * POST /rules           — create throttle rule (auth)
 * GET  /events          — list throttle events (auth)
 * GET  /admin/overview  — platform-wide stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiThrottlingService } from '../services/tenant-api-throttling';

// Inline Bindings type — keeps this file self-contained
type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── Tenant routes (JWT / API key auth) ────────────────────────────────────────

/**
 * GET /rules — list all throttle rules for the authenticated tenant
 */
app.get('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiThrottlingService.listRules(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to list throttle rules' }, 500);
  }
});

/**
 * POST /rules — create a new throttle rule for the authenticated tenant
 * Body: { rule_name, endpoint_pattern, max_concurrent?, queue_timeout_ms? }
 */
app.post('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      rule_name?: string;
      endpoint_pattern?: string;
      max_concurrent?: number;
      queue_timeout_ms?: number;
    };

    const ruleName = body.rule_name?.trim();
    const endpointPattern = body.endpoint_pattern?.trim();

    if (!ruleName || !endpointPattern) {
      return c.json({ error: 'rule_name and endpoint_pattern are required' }, 400);
    }

    const result = await tenantApiThrottlingService.createRule(c.env.DB, tenantId, {
      rule_name: ruleName,
      endpoint_pattern: endpointPattern,
      max_concurrent: body.max_concurrent,
      queue_timeout_ms: body.queue_timeout_ms,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create throttle rule' }, 500);
  }
});

/**
 * GET /events — list throttle events for the authenticated tenant
 * Query: limit (default 50, max 200), rule_id (optional filter)
 */
app.get('/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const ruleId = c.req.query('rule_id');

    const result = await tenantApiThrottlingService.getEvents(c.env.DB, tenantId, {
      limit,
      ruleId: ruleId ?? undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to list throttle events' }, 500);
  }
});

// ── Admin route (X-Admin-Key) ──────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide throttle stats across all tenants
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await tenantApiThrottlingService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiThrottling };
