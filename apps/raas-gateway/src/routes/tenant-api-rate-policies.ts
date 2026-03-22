/**
 * Tenant API Rate Policies routes
 * Mount at: /v1/rate-policies
 *
 * GET  /policies          — list tenant's rate policies (auth required)
 * POST /policies          — create rate policy (auth required)
 * GET  /violations        — list tenant's violations (auth required)
 * GET  /admin/overview    — cross-tenant overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiRatePoliciesService } from '../services/tenant-api-rate-policies';

// Inline Bindings type — mirrors Env without importing from index.ts
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /policies — list rate policies for the authenticated tenant
 */
app.get('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiRatePoliciesService.listPolicies(c.env.DB, tenantId);
    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /policies] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /policies — create a new rate policy for the authenticated tenant
 * Body: { policy_name, endpoint_pattern, requests_per_minute?, burst_size?, status? }
 */
app.post('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.policy_name || !body.endpoint_pattern) {
      return c.json({ error: 'policy_name and endpoint_pattern are required' }, 400);
    }

    const result = await tenantApiRatePoliciesService.createPolicy(c.env.DB, tenantId, body);
    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[POST /policies] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /violations — list rate policy violations for the authenticated tenant
 */
app.get('/violations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiRatePoliciesService.getViolations(c.env.DB, tenantId);
    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /violations] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — cross-tenant policy+violation summary
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantApiRatePoliciesService.getAdminOverview(c.env.DB);
    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /admin/overview] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiRatePolicies };
