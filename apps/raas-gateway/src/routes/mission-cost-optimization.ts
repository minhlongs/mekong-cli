/**
 * Mission Cost Optimization routes — tenant rule management + admin overview
 *
 * Tenant (auth required):
 *   GET  /rules          — list cost optimization rules
 *   POST /rules          — create a new rule
 *   GET  /events         — list optimization events
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — aggregate savings overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionCostOptimizationService as svc } from '../services/mission-cost-optimization-service';

const app = new Hono<{ Bindings: Env }>();

/** GET /rules — list tenant cost optimization rules */
app.get('/rules', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const rules = await svc.listRules(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: rules });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return c.json({ error: message, code: 'DB_ERROR' }, 500);
  }
});

/** POST /rules — create a cost optimization rule */
app.post('/rules', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, 400);
  }
  if (!body.rule_name || typeof body.rule_name !== 'string') {
    return c.json({ error: 'rule_name required', code: 'BAD_REQUEST' }, 400);
  }
  try {
    const rule = await svc.createRule(c.env.DB, tenant.tenantId, {
      rule_name: body.rule_name,
      condition_json: body.condition_json as string | undefined,
      action_type: body.action_type as string | undefined,
      savings_estimate: body.savings_estimate as number | undefined,
    });
    return c.json({ success: true, data: rule }, 201);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return c.json({ error: message, code: 'DB_ERROR' }, 500);
  }
});

/** GET /events — list cost optimization events for tenant */
app.get('/events', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '50', 10), 1), 200);
  try {
    const events = await svc.getEvents(c.env.DB, tenant.tenantId, limit);
    return c.json({ success: true, data: events });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return c.json({ error: message, code: 'DB_ERROR' }, 500);
  }
});

/** GET /admin/overview — aggregate savings across all tenants (admin only) */
app.get('/admin/overview', async (c) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return c.json({ error: message, code: 'DB_ERROR' }, 500);
  }
});

export { app as missionCostOptimization };
