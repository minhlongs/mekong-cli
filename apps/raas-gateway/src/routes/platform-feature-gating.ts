/**
 * Platform Feature Gating routes — admin-only tier-based feature access control
 *
 * All routes require X-Admin-Key header.
 *
 *   GET  /gates       — list all feature gates
 *   POST /gates       — create a new feature gate
 *   GET  /overrides   — list overrides (query: gate_id, tenant_id)
 *   GET  /dashboard   — summary: counts + gate list
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformFeatureGatingService as svc } from '../services/platform-feature-gating-service';

export const platformFeatureGating = new Hono<{ Bindings: Env }>();

// Admin-only guard — 403 on missing/wrong key
platformFeatureGating.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  await next();
});

/** GET /gates — list all feature gates */
platformFeatureGating.get('/gates', async (c) => {
  try {
    const gates = await svc.listGates(c.env.DB);
    return c.json({ success: true, data: gates });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ success: false, error }, 500);
  }
});

/** POST /gates — create feature gate; body: { feature_key, display_name, description?, allowed_tiers? } */
platformFeatureGating.post('/gates', async (c) => {
  try {
    type Body = { feature_key: string; display_name: string; description?: string; allowed_tiers?: string };
    const body = await c.req.json<Body>();
    if (!body.feature_key || !body.display_name) {
      return c.json({ success: false, error: 'feature_key and display_name are required' }, 400);
    }
    const gate = await svc.createGate(c.env.DB, body);
    return c.json({ success: true, data: gate }, 201);
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ success: false, error }, 500);
  }
});

/** GET /overrides?gate_id=&tenant_id= — list overrides filtered by gate or tenant */
platformFeatureGating.get('/overrides', async (c) => {
  try {
    const gate_id = c.req.query('gate_id');
    const tenant_id = c.req.query('tenant_id');
    const overrides = await svc.getOverrides(c.env.DB, { gate_id, tenant_id });
    return c.json({ success: true, data: overrides });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ success: false, error }, 500);
  }
});

/** GET /dashboard — summary stats + full gate list */
platformFeatureGating.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json({ success: true, data: dashboard });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ success: false, error }, 500);
  }
});
