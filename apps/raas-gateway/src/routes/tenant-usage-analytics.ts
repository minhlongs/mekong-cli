/**
 * Tenant Usage Analytics routes — detailed API usage per tenant
 * Auth: GET /analytics, POST /analytics, GET /summaries
 * Admin: GET /admin/overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantUsageAnalyticsService } from '../services/tenant-usage-analytics';

const app = new Hono<{ Bindings: Env }>();

// ── Auth routes ────────────────────────────────────────────────────────────────

/**
 * GET /analytics — list recent API usage records for authenticated tenant
 * Query: limit (default 50)
 */
app.get('/analytics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(Number(c.req.query('limit') ?? 50), 200);
    const result = await tenantUsageAnalyticsService.listAnalytics(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ analytics: result.data, total: result.data?.length ?? 0 });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/**
 * POST /analytics — record a new API usage entry for authenticated tenant
 * Body: { endpoint, method, status_code?, response_time_ms?, request_size?, response_size? }
 */
app.post('/analytics', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

    const endpoint = String(body.endpoint ?? '').trim();
    const method = String(body.method ?? '').trim();

    if (!endpoint) return c.json({ error: 'endpoint is required' }, 400);
    if (!method) return c.json({ error: 'method is required' }, 400);

    const result = await tenantUsageAnalyticsService.createAnalytic(
      c.env.DB,
      tenantId,
      endpoint,
      method,
      body.status_code != null ? Number(body.status_code) : undefined,
      body.response_time_ms != null ? Number(body.response_time_ms) : undefined,
      body.request_size != null ? Number(body.request_size) : undefined,
      body.response_size != null ? Number(body.response_size) : undefined
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ analytic: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/**
 * GET /summaries — list period summaries for authenticated tenant
 * Query: limit (default 30)
 */
app.get('/summaries', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(Number(c.req.query('limit') ?? 30), 90);
    const result = await tenantUsageAnalyticsService.getSummaries(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ summaries: result.data, total: result.data?.length ?? 0 });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// ── Admin route ────────────────────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide usage stats across all tenants (X-Admin-Key required)
 */
app.get('/admin/overview', async (c) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await tenantUsageAnalyticsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as tenantUsageAnalytics };
