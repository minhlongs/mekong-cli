/**
 * Webhook Analytics routes — delivery stats, timeline, endpoint health, admin overview
 * Tenant routes require auth middleware; admin route requires X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { auth, getTenant } from '../middleware/auth';
import {
  getDeliveryStats,
  getDeliveryTimeline,
  listEndpoints,
  getFailedEndpoints,
  resetEndpointHealth,
  getWebhookOverview,
  getAdminWebhookAnalytics,
} from '../services/webhook-analytics-service';

const app = new Hono<{ Bindings: Env }>();

// ── Tenant routes (auth required) ───────────────────────────────────────────

app.use('/stats', auth());
app.use('/timeline', auth());
app.use('/endpoints', auth());
app.use('/endpoints/failed', auth());
app.use('/endpoints/reset', auth());
app.use('/overview', auth());

/** GET /stats — aggregated delivery stats for the authenticated tenant */
app.get('/stats', async (c) => {
  const tenant = getTenant(c);
  try {
    const days = Math.min(parseInt(c.req.query('days') ?? '7'), 90);
    const stats = await getDeliveryStats(c.env.DB, tenant.tenantId, days);
    return json({ stats, tenant_id: tenant.tenantId, period_days: days });
  } catch {
    return json({ error: 'Failed to fetch delivery stats', code: 'STATS_ERROR' }, { status: 500 });
  }
});

/** GET /timeline — day-by-day delivery breakdown, ?days=30 (max 90) */
app.get('/timeline', async (c) => {
  const tenant = getTenant(c);
  try {
    const days = Math.min(parseInt(c.req.query('days') ?? '30'), 90);
    const timeline = await getDeliveryTimeline(c.env.DB, tenant.tenantId, days);
    return json({ timeline, count: timeline.length, period_days: days });
  } catch {
    return json({ error: 'Failed to fetch delivery timeline', code: 'TIMELINE_ERROR' }, { status: 500 });
  }
});

/** GET /endpoints — list all endpoint health records for the tenant */
app.get('/endpoints', async (c) => {
  const tenant = getTenant(c);
  try {
    const endpoints = await listEndpoints(c.env.DB, tenant.tenantId);
    return json({ endpoints, count: endpoints.length });
  } catch {
    return json({ error: 'Failed to list endpoints', code: 'LIST_ERROR' }, { status: 500 });
  }
});

/** GET /endpoints/failed — endpoints with degraded or down status */
app.get('/endpoints/failed', async (c) => {
  const tenant = getTenant(c);
  try {
    const endpoints = await getFailedEndpoints(c.env.DB, tenant.tenantId);
    return json({ endpoints, count: endpoints.length });
  } catch {
    return json({ error: 'Failed to fetch failed endpoints', code: 'FAILED_ENDPOINTS_ERROR' }, { status: 500 });
  }
});

/** POST /endpoints/reset — reset a specific endpoint back to healthy */
app.post('/endpoints/reset', async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{ endpoint_url: string }>();
    if (!body.endpoint_url) {
      return json({ error: 'endpoint_url is required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const ok = await resetEndpointHealth(c.env.DB, tenant.tenantId, body.endpoint_url);
    if (!ok) {
      return json({ error: 'Endpoint not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ reset: true, endpoint_url: body.endpoint_url });
  } catch {
    return json({ error: 'Failed to reset endpoint', code: 'RESET_ERROR' }, { status: 500 });
  }
});

/** GET /overview — high-level webhook summary (30-day stats + endpoint health counts) */
app.get('/overview', async (c) => {
  const tenant = getTenant(c);
  try {
    const overview = await getWebhookOverview(c.env.DB, tenant.tenantId);
    return json({ overview, tenant_id: tenant.tenantId });
  } catch {
    return json({ error: 'Failed to fetch webhook overview', code: 'OVERVIEW_ERROR' }, { status: 500 });
  }
});

// ── Admin route (X-Admin-Key required) ─────────────────────────────────────

/** GET /admin/analytics — cross-tenant webhook analytics, admin only */
app.get('/admin/analytics', async (c) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  try {
    const analytics = await getAdminWebhookAnalytics(c.env.DB);
    return json({ analytics });
  } catch {
    return json({ error: 'Failed to fetch admin analytics', code: 'ADMIN_ANALYTICS_ERROR' }, { status: 500 });
  }
});

export { app as webhookAnalytics };
