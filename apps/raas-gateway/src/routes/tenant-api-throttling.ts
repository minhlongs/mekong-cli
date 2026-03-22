/**
 * Tenant API Throttling Routes
 * Per-tenant endpoint throttle rules and event log management.
 *
 * GET  /rules           — list throttle rules (auth)
 * POST /rules           — create throttle rule (auth)
 * GET  /events          — list throttle events (auth)
 * GET  /admin/overview  — admin stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiThrottlingService } from '../services/tenant-api-throttling';

const app = new Hono<{ Bindings: Env }>();

// GET /rules — list all throttle rules for authenticated tenant
app.get('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const rules = await tenantApiThrottlingService.listRules(c.env.DB, tenantId);
    return c.json({ rules, total: rules.length });
  } catch (err) {
    return c.json({ error: 'Failed to list throttle rules' }, 500);
  }
});

// POST /rules — create a new throttle rule
app.post('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      endpoint_pattern?: string;
      requests_per_minute?: number;
      burst_limit?: number;
    };

    const endpoint_pattern = body.endpoint_pattern?.trim();
    if (!endpoint_pattern) {
      return c.json({ error: 'endpoint_pattern is required', code: 'VALIDATION_ERROR' }, 400);
    }

    const rule = await tenantApiThrottlingService.createRule(c.env.DB, tenantId, {
      endpoint_pattern,
      requests_per_minute: body.requests_per_minute,
      burst_limit: body.burst_limit,
    });

    return c.json(rule, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create throttle rule' }, 500);
  }
});

// GET /events — list throttle events for authenticated tenant
app.get('/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const events = await tenantApiThrottlingService.getEvents(c.env.DB, tenantId);
    return c.json({ events, total: events.length });
  } catch (err) {
    return c.json({ error: 'Failed to list throttle events' }, 500);
  }
});

// GET /admin/overview — admin stats across all tenants (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }

  try {
    const overview = await tenantApiThrottlingService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiThrottling };
