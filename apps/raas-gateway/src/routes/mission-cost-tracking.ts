/**
 * Mission Cost Tracking routes — record and query AI provider costs per mission
 * GET  /costs          — list tenant costs
 * POST /costs          — record a cost entry
 * GET  /budgets        — list tenant budgets
 * GET  /admin/overview — cross-tenant spend overview (X-Admin-Key protected)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionCostTrackingService } from '../services/mission-cost-tracking';
import { json } from '../utils/response';

const app = new Hono<{ Bindings: Env }>();

/**
 * GET /costs — list all cost records for the authenticated tenant
 */
app.get('/costs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const costs = await missionCostTrackingService.listCosts(c.env.DB, tenant.tenantId);
    return json({ costs, total: costs.length });
  } catch (err) {
    return json({ error: 'Failed to list costs' }, { status: 500 });
  }
});

/**
 * POST /costs — record a new cost entry for the authenticated tenant
 * Body: { mission_id, cost_type, amount, currency?, provider?, model?, tokens_used? }
 */
app.post('/costs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    const { mission_id, cost_type, amount } = body;

    if (!mission_id || typeof mission_id !== 'string') {
      return json({ error: 'mission_id is required', code: 'INVALID_INPUT' }, { status: 400 });
    }
    if (!cost_type || typeof cost_type !== 'string') {
      return json({ error: 'cost_type is required', code: 'INVALID_INPUT' }, { status: 400 });
    }
    if (typeof amount !== 'number' || amount < 0) {
      return json({ error: 'amount must be a non-negative number', code: 'INVALID_INPUT' }, { status: 400 });
    }

    const cost = await missionCostTrackingService.recordCost(c.env.DB, tenant.tenantId, {
      mission_id,
      cost_type,
      amount,
      currency: body.currency,
      provider: body.provider,
      model: body.model,
      tokens_used: body.tokens_used,
    });

    if (!cost) {
      return json({ error: 'Failed to record cost' }, { status: 500 });
    }

    return json(cost, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to record cost' }, { status: 500 });
  }
});

/**
 * GET /budgets — list budget records for the authenticated tenant
 */
app.get('/budgets', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const budgets = await missionCostTrackingService.getBudgets(c.env.DB, tenant.tenantId);
    return json({ budgets, total: budgets.length });
  } catch (err) {
    return json({ error: 'Failed to list budgets' }, { status: 500 });
  }
});

/**
 * GET /admin/overview — cross-tenant spend overview, requires X-Admin-Key header
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    const expected = c.env.ADMIN_API_KEY;
    if (!expected || key !== expected) {
      return json({ error: 'Forbidden', code: 'INVALID_ADMIN_KEY' }, { status: 403 });
    }

    const overview = await missionCostTrackingService.getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err) {
    return json({ error: 'Failed to load admin overview' }, { status: 500 });
  }
});

export { app as missionCostTracking };
