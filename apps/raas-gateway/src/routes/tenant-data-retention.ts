/**
 * Tenant Data Retention routes
 * Mount at: /v1/data-retention
 *
 * GET  /policies         — list tenant's retention policies
 * POST /policies         — create a new retention policy
 * GET  /executions       — list execution history for tenant
 * GET  /admin/overview   — platform-wide overview (admin only)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantDataRetentionService } from '../services/tenant-data-retention';

type Bindings = {
  DB: any;
  ADMIN_KEY?: string;
};

const app = new Hono<{ Bindings: Bindings }>();

/** GET /policies — list all retention policies for authenticated tenant */
app.get('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantDataRetentionService.listPolicies(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[data-retention GET /policies] error:', err);
    return c.json({ error: 'Failed to list retention policies' }, 500);
  }
});

/** POST /policies — create a retention policy for authenticated tenant */
app.post('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const result = await tenantDataRetentionService.createPolicy(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[data-retention POST /policies] error:', err);
    return c.json({ error: 'Failed to create retention policy' }, 500);
  }
});

/** GET /executions — list execution history for authenticated tenant */
app.get('/executions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantDataRetentionService.getExecutions(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[data-retention GET /executions] error:', err);
    return c.json({ error: 'Failed to fetch executions' }, 500);
  }
});

/** GET /admin/overview — platform-wide retention overview, requires X-Admin-Key */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantDataRetentionService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[data-retention GET /admin/overview] error:', err);
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantDataRetention };
