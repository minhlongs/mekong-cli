/**
 * Tenant API Response Transform Routes — manage per-tenant response transform rules
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantApiResponseTransformService as svc } from '../services/tenant-api-response-transform-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/transforms', auth());
app.use('/transforms/*', auth());
app.use('/logs', auth());

/** GET /transforms — list transform rules for authenticated tenant */
app.get('/transforms', async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await svc.listTransforms(c.env.DB, tenant.tenantId);
    return json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to list transforms';
    return json({ error: msg, code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /transforms — create a new transform rule */
app.post('/transforms', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    if (!body.rule_name || !body.match_pattern) {
      return json({ error: 'rule_name and match_pattern are required', code: 'INVALID_INPUT' }, { status: 400 });
    }

    const transform = await svc.createTransform(c.env.DB, tenant.tenantId, {
      rule_name: body.rule_name,
      match_pattern: body.match_pattern,
      transform_type: body.transform_type,
      transform_config: body.transform_config,
      priority: body.priority,
    });

    return json({ transform }, { status: 201 });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create transform';
    return json({ error: msg, code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /logs — get transform execution logs for authenticated tenant */
app.get('/logs', async (c) => {
  try {
    const tenant = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '100', 10) || 100, 500);
    const result = await svc.getLogs(c.env.DB, tenant.tenantId, limit);
    return json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to get logs';
    return json({ error: msg, code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /admin/overview — admin-only aggregate stats across all tenants */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin access required', code: 'FORBIDDEN' }, { status: 403 });
  }

  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to get admin overview';
    return json({ error: msg, code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

export { app as tenantApiResponseTransform };
