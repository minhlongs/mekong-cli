/**
 * Platform Feature Usage routes — admin-only endpoints for feature usage tracking
 * All routes require X-Admin-Key header; returns 403 on mismatch
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { platformFeatureUsageService } from '../services/platform-feature-usage';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard — all routes require X-Admin-Key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

/** GET /usage?feature_name=&tenant_id=&period= — list usage records */
app.get('/usage', async (c) => {
  try {
    const feature_name = c.req.query('feature_name');
    const tenant_id = c.req.query('tenant_id');
    const period = c.req.query('period');
    const data = await platformFeatureUsageService.listUsage(c.env.DB, { feature_name, tenant_id, period });
    return json({ usage: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /usage — record a feature usage event */
app.post('/usage', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.id || !body.feature_name || !body.tenant_id) {
      return json({ error: 'id, feature_name, and tenant_id are required' }, { status: 400 });
    }
    const result = await platformFeatureUsageService.recordUsage(c.env.DB, body);
    return json(result, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /adoption?feature_name= — get feature adoption metrics */
app.get('/adoption', async (c) => {
  try {
    const feature_name = c.req.query('feature_name');
    const data = await platformFeatureUsageService.getAdoption(c.env.DB, feature_name);
    return json({ adoption: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /dashboard — summary dashboard: top features by usage and adoption */
app.get('/dashboard', async (c) => {
  try {
    const data = await platformFeatureUsageService.getDashboard(c.env.DB);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

export { app as platformFeatureUsage };
