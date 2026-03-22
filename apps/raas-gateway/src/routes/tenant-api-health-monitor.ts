/**
 * Tenant API Health Monitor routes
 * Mount at: /v1/api-health-monitors
 *
 * Tenant routes (auth required):
 *   GET  /monitors          — list monitors for authenticated tenant
 *   POST /monitors          — create a new monitor
 *   GET  /results           — get check results for a monitor (query: monitor_id, limit)
 *
 * Admin route (X-Admin-Key required):
 *   GET  /admin/overview    — platform-wide monitor stats + recent unhealthy checks
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiHealthMonitorService } from '../services/tenant-api-health-monitor';

// Inline Bindings — avoids circular import from index.ts
interface Bindings {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: any;
}

const app = new Hono<{ Bindings: Bindings }>();

// ---- Tenant routes (JWT / API key auth) ------------------------------------

/**
 * GET /monitors — list all monitors for the authenticated tenant
 */
app.get('/monitors', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiHealthMonitorService.listMonitors(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[tenant-api-health-monitor GET /monitors]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /monitors — create a new endpoint health monitor
 * Body: { monitor_name, endpoint_url, check_interval_ms?, expected_status? }
 */
app.post('/monitors', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.monitor_name || !body.endpoint_url) {
      return c.json({ error: 'monitor_name and endpoint_url are required' }, 400);
    }

    const result = await tenantApiHealthMonitorService.createMonitor(c.env.DB, tenantId, {
      monitor_name: body.monitor_name,
      endpoint_url: body.endpoint_url,
      check_interval_ms: body.check_interval_ms,
      expected_status: body.expected_status,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[tenant-api-health-monitor POST /monitors]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /results — get check results for a specific monitor
 * Query: monitor_id (required), limit (optional, default 20)
 */
app.get('/results', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const monitorId = c.req.query('monitor_id');
    const limit = parseInt(c.req.query('limit') ?? '20', 10) || 20;

    if (!monitorId) {
      return c.json({ error: 'monitor_id query parameter is required' }, 400);
    }

    const result = await tenantApiHealthMonitorService.getResults(
      c.env.DB,
      tenantId,
      monitorId,
      limit
    );

    if (!result.success) return c.json({ error: result.error }, 404);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[tenant-api-health-monitor GET /results]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ---- Admin route (X-Admin-Key) ---------------------------------------------

/**
 * GET /admin/overview — platform-wide monitor stats and recent unhealthy checks
 * Requires X-Admin-Key header matching ADMIN_KEY env binding
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantApiHealthMonitorService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[tenant-api-health-monitor GET /admin/overview]', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiHealthMonitor };
