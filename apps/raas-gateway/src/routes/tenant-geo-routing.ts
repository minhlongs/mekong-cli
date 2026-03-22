/**
 * Tenant Geo Routing routes — per-tenant geographic routing rules and analytics
 * GET  /rules          — list tenant rules (auth required)
 * POST /rules          — create tenant rule (auth required)
 * GET  /analytics      — tenant analytics, optional ?rule_id= (auth required)
 * GET  /admin/overview — cross-tenant aggregation (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantGeoRoutingService as svc } from '../services/tenant-geo-routing';

interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

// ── Admin: cross-tenant overview ──────────────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── Tenant: list geo routing rules ───────────────────────────────────────────

app.get('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listRules(c.env.DB, tenantId);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── Tenant: create geo routing rule ──────────────────────────────────────────

app.post('/rules', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      rule_name: string;
      source_region: string;
      target_endpoint: string;
      priority?: number;
      enabled?: number;
    }>();

    if (!body.rule_name?.trim()) return c.json({ success: false, error: 'rule_name is required' }, 400);
    if (!body.source_region?.trim()) return c.json({ success: false, error: 'source_region is required' }, 400);
    if (!body.target_endpoint?.trim()) return c.json({ success: false, error: 'target_endpoint is required' }, 400);

    const result = await svc.createRule(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── Tenant: get analytics (optional ?rule_id=) ───────────────────────────────

app.get('/analytics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const ruleId = c.req.query('rule_id');
    const result = await svc.getAnalytics(c.env.DB, tenantId, ruleId);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as tenantGeoRouting };
