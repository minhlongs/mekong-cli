/**
 * Tenant API Access Logs routes
 * Mount at: /v1/access-logs
 *
 * GET  /logs           — list logs for authenticated tenant
 * POST /logs           — create a log entry for authenticated tenant
 * GET  /exports        — list export jobs for authenticated tenant
 * POST /exports        — create an export job for authenticated tenant
 * GET  /admin/overview — platform-wide stats (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiAccessLogsService } from '../services/tenant-api-access-logs';

type Bindings = {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/** GET /logs — list access logs for authenticated tenant */
app.get('/logs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const offset = parseInt(c.req.query('offset') ?? '0', 10) || 0;
    const result = await tenantApiAccessLogsService.listLogs(c.env.DB, tenant.tenantId, limit, offset);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** POST /logs — create an access log entry for authenticated tenant */
app.post('/logs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json();
    const result = await tenantApiAccessLogsService.createLog(c.env.DB, tenant.tenantId, {
      userId: body.user_id,
      method: body.method,
      path: body.path,
      statusCode: body.status_code,
      ipAddress: body.ip_address ?? c.req.header('CF-Connecting-IP'),
      userAgent: body.user_agent ?? c.req.header('User-Agent'),
      country: body.country ?? c.req.header('CF-IPCountry'),
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /exports — list export jobs for authenticated tenant */
app.get('/exports', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await tenantApiAccessLogsService.getExports(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** POST /exports — create an export job for authenticated tenant */
app.post('/exports', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json();
    const result = await tenantApiAccessLogsService.createExport(
      c.env.DB,
      tenant.tenantId,
      body.format ?? 'csv',
      body.date_from,
      body.date_to
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/overview — platform-wide stats, requires X-Admin-Key header */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const result = await tenantApiAccessLogsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as tenantApiAccessLogs };
