/**
 * Mission Cost Tracking routes — record and query execution costs per mission
 *
 * Tenant (auth required):
 *   GET  /costs     — list cost records
 *   POST /costs     — create a cost entry
 *   GET  /budgets   — list budget records
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — cross-tenant spend overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionCostTrackingService } from '../services/mission-cost-tracking';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

/** GET /costs — list cost records for the authenticated tenant */
app.get('/costs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await missionCostTrackingService.listCosts(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list costs' }, 500);
  }
});

/** POST /costs — record a new cost entry for the authenticated tenant */
app.post('/costs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    let body: Record<string, unknown>;
    try {
      body = await c.req.json();
    } catch {
      return c.json({ error: 'Invalid JSON' }, 400);
    }

    const { mission_id, cost_type, amount } = body;
    if (!mission_id || typeof mission_id !== 'string') {
      return c.json({ error: 'mission_id is required' }, 400);
    }
    if (!cost_type || typeof cost_type !== 'string') {
      return c.json({ error: 'cost_type is required' }, 400);
    }
    if (typeof amount !== 'number' || amount < 0) {
      return c.json({ error: 'amount must be a non-negative number' }, 400);
    }

    const result = await missionCostTrackingService.createCost(c.env.DB, tenant.tenantId, {
      mission_id,
      cost_type,
      amount,
      currency: body.currency as string | undefined,
      provider: body.provider as string | undefined,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create cost' }, 500);
  }
});

/** GET /budgets — list budget records for the authenticated tenant */
app.get('/budgets', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await missionCostTrackingService.getBudgets(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list budgets' }, 500);
  }
});

/** GET /admin/overview — cross-tenant spend overview (X-Admin-Key protected) */
app.get('/admin/overview', async (c) => {
  try {
    if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const result = await missionCostTrackingService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to load admin overview' }, 500);
  }
});

export { app as missionCostTracking };
