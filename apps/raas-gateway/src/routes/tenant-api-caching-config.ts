/**
 * Tenant API Caching Config routes
 * Mount at: /v1/caching
 *
 * GET  /configs          — list tenant's caching configs (auth required)
 * POST /configs          — create caching config (auth required)
 * GET  /stats            — tenant cache hit/miss stats (auth required)
 * GET  /admin/overview   — platform-wide overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiCachingConfigService } from '../services/tenant-api-caching-config';

// Inline Bindings — avoids import of Env from index.ts
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /configs — list all caching configs for authenticated tenant
 */
app.get('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiCachingConfigService.listConfigs(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[caching GET /configs] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /configs — create a new caching config for authenticated tenant
 * Body: { endpoint_pattern, ttl_seconds?, cache_key_template?, enabled? }
 */
app.post('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.endpoint_pattern || typeof body.endpoint_pattern !== 'string') {
      return c.json({ error: 'endpoint_pattern is required and must be a string' }, 400);
    }

    const result = await tenantApiCachingConfigService.createConfig(c.env.DB, tenantId, {
      endpoint_pattern: body.endpoint_pattern,
      ttl_seconds: typeof body.ttl_seconds === 'number' ? body.ttl_seconds : undefined,
      cache_key_template: typeof body.cache_key_template === 'string' ? body.cache_key_template : undefined,
      enabled: typeof body.enabled === 'number' ? body.enabled : undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[caching POST /configs] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /stats — cache hit/miss stats for authenticated tenant
 * Query param: config_id (optional, filter by specific config)
 */
app.get('/stats', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.query('config_id') || undefined;
    const result = await tenantApiCachingConfigService.getStats(c.env.DB, tenantId, configId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[caching GET /stats] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide caching overview
 * Protected by X-Admin-Key header
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    const expected = c.env.ADMIN_API_KEY;
    if (!expected || key !== expected) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantApiCachingConfigService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[caching GET /admin/overview] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiCachingConfig };
