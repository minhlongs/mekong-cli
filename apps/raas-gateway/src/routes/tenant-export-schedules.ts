/**
 * Tenant Export Schedules routes — schedule management and run history
 *
 * Tenant (auth):
 *   GET  /schedules  — list tenant export schedules
 *   POST /schedules  — create export schedule
 *   GET  /runs       — list tenant export run history
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — platform-wide export stats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantExportSchedulesService as svc } from '../services/tenant-export-schedules';

const app = new Hono<{ Bindings: Env }>();

// GET /schedules — list all export schedules for authenticated tenant
app.get('/schedules', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const schedules = await svc.listSchedules(c.env.DB, tenant.tenantId);
    return c.json({ schedules, count: schedules.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /schedules — create a new export schedule for authenticated tenant
app.post('/schedules', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      export_type: string;
      format?: string;
      cron_expression: string;
      destination: string;
      is_active?: number;
    }>();
    if (!body.export_type) return c.json({ error: 'export_type is required' }, 400);
    if (!body.cron_expression) return c.json({ error: 'cron_expression is required' }, 400);
    if (!body.destination) return c.json({ error: 'destination is required' }, 400);

    const schedule = await svc.createSchedule(c.env.DB, tenant.tenantId, body);
    return c.json(schedule, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /runs — list export run history for authenticated tenant
app.get('/runs', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const runs = await svc.getRuns(c.env.DB, tenant.tenantId);
    return c.json({ runs, count: runs.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — platform-wide export stats (admin only)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as tenantExportSchedules };
