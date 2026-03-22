/**
 * Admin Platform Health Dashboard routes — health checks + incidents + aggregated dashboard
 * All endpoints: X-Admin-Key required (403 on missing/invalid)
 * GET  /checks          — list all health checks (optional ?service_name=)
 * POST /checks          — create a new health check record
 * GET  /incidents       — list incidents (optional ?service_name= &unresolved=true)
 * GET  /dashboard       — aggregated health dashboard summary
 */

import { Hono } from 'hono';
import { adminPlatformHealthDashboardService } from '../services/admin-platform-health-dashboard';

// Inline Bindings — no import from index to avoid circular deps
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — all routes require valid X-Admin-Key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /checks — list health checks, optional ?service_name= filter
app.get('/checks', async (c) => {
  try {
    const service_name = c.req.query('service_name');
    const result = await adminPlatformHealthDashboardService.listChecks(c.env.DB, service_name);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /checks — create a new health check record
// Body: { id, service_name, check_type?, status?, response_time_ms? }
app.post('/checks', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const { id, service_name, check_type, status, response_time_ms } = body as {
      id?: string;
      service_name?: string;
      check_type?: string;
      status?: string;
      response_time_ms?: number;
    };

    if (!id || !service_name) {
      return c.json({ error: 'id and service_name are required' }, 400);
    }

    const result = await adminPlatformHealthDashboardService.createCheck(c.env.DB, {
      id,
      service_name,
      check_type,
      status,
      response_time_ms,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /incidents — list incidents, optional ?service_name= and ?unresolved=true filters
app.get('/incidents', async (c) => {
  try {
    const service_name = c.req.query('service_name');
    const unresolved_only = c.req.query('unresolved') === 'true';
    const result = await adminPlatformHealthDashboardService.getIncidents(
      c.env.DB,
      service_name,
      unresolved_only
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /dashboard — aggregated platform health summary
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformHealthDashboardService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminPlatformHealthDashboard };
