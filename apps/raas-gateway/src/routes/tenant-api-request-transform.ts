/**
 * Tenant API Request Transform routes
 * Mount at: /v1/transforms
 *
 * GET  /transforms          — list transforms for authenticated tenant
 * POST /transforms          — create transform rule for authenticated tenant
 * GET  /logs                — get transform logs for authenticated tenant
 * GET  /admin/overview      — admin overview across all tenants (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiRequestTransformService } from '../services/tenant-api-request-transform';

// Inline Bindings type to avoid coupling with index.ts
type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /transforms — list all transform rules for the authenticated tenant
 */
app.get('/transforms', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiRequestTransformService.listTransforms(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /transforms]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /transforms — create a new transform rule for the authenticated tenant
 * Body: { transform_name, source_path, target_path, transform_type?, transform_config?, enabled? }
 */
app.post('/transforms', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.transform_name || !body.source_path || !body.target_path) {
      return c.json({ error: 'transform_name, source_path, and target_path are required' }, 400);
    }

    const result = await tenantApiRequestTransformService.createTransform(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[POST /transforms]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /logs — get transform application logs for the authenticated tenant
 * Query: limit (default 50, max 200)
 */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const result = await tenantApiRequestTransformService.getLogs(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /logs]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide transform stats (admin only)
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const result = await tenantApiRequestTransformService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /admin/overview]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiRequestTransform };
