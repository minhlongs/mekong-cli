/**
 * API Gateway Caching routes — cache config CRUD, invalidation, stats, analytics
 *
 * Auth:  GET /configs  POST /configs  PUT /configs/:configId  DELETE /configs/:configId
 *        POST /invalidate  GET /stats  GET /analytics
 * Admin: GET /admin/overview  (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createCacheConfig,
  listCacheConfigs,
  updateCacheConfig,
  deleteCacheConfig,
  invalidateCache,
} from '../services/api-gateway-caching-service';
import {
  getCacheStats,
  getCacheAnalytics,
  getAdminCacheOverview,
} from '../services/api-gateway-caching-analytics-service';

const app = new Hono<{ Bindings: Env }>();

/** Admin key guard */
function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── GET /configs — list cache configs ────────────────────────────────────────
app.get('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configs = await listCacheConfigs(c.env.DB, tenantId);
    return json({ success: true, data: configs });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to list cache configs' }, { status: 500 });
  }
});

// ── POST /configs — create cache config ──────────────────────────────────────
app.post('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      path_pattern: string;
      method?: string;
      ttl_seconds?: number;
      vary_headers?: string[];
      vary_query_params?: string[];
      is_active?: boolean;
      cache_scope?: string;
      max_size_bytes?: number;
    }>();

    if (!body.path_pattern) {
      return json({ error: 'path_pattern is required' }, { status: 400 });
    }

    const config = await createCacheConfig(c.env.DB, tenantId, body);
    return json({ success: true, data: config }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to create cache config' }, { status: 500 });
  }
});

// ── PUT /configs/:configId — update cache config ──────────────────────────────
app.put('/configs/:configId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.param('configId');
    const body = await c.req.json();
    const updated = await updateCacheConfig(c.env.DB, configId, tenantId, body);
    if (!updated) return json({ error: 'Cache config not found' }, { status: 404 });
    return json({ success: true, data: updated });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to update cache config' }, { status: 500 });
  }
});

// ── DELETE /configs/:configId — delete cache config ───────────────────────────
app.delete('/configs/:configId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.param('configId');
    const deleted = await deleteCacheConfig(c.env.DB, configId, tenantId);
    if (!deleted) return json({ error: 'Cache config not found' }, { status: 404 });
    return json({ success: true, data: { deleted: true } });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to delete cache config' }, { status: 500 });
  }
});

// ── POST /invalidate — invalidate cache entries ───────────────────────────────
app.post('/invalidate', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ path_pattern?: string }>().catch(() => ({ path_pattern: undefined }));
    const count = await invalidateCache(c.env.DB, tenantId, body.path_pattern);
    return json({ success: true, data: { invalidated: count } });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to invalidate cache' }, { status: 500 });
  }
});

// ── GET /stats — cache stats for tenant ──────────────────────────────────────
app.get('/stats', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const stats = await getCacheStats(c.env.DB, tenantId);
    return json({ success: true, data: stats });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to fetch cache stats' }, { status: 500 });
  }
});

// ── GET /analytics — cache analytics with optional date range ─────────────────
app.get('/analytics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const from = c.req.query('from');
    const to = c.req.query('to');
    const analytics = await getCacheAnalytics(c.env.DB, tenantId, from, to);
    return json({ success: true, data: analytics });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to fetch cache analytics' }, { status: 500 });
  }
});

// ── GET /admin/overview — platform-wide cache overview ────────────────────────
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Admin key required' }, { status: 401 });
  try {
    const overview = await getAdminCacheOverview(c.env.DB);
    return json({ success: true, data: overview });
  } catch (e: unknown) {
    return json({ error: e instanceof Error ? e.message : 'Failed to fetch admin overview' }, { status: 500 });
  }
});

export const apiGatewayCaching = app;
