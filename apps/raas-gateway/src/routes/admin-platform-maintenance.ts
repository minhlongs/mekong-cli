/**
 * Admin Platform Maintenance routes — schedule and manage platform maintenance windows
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-maintenance
 */

import { Hono } from 'hono';
import { adminPlatformMaintenanceService as svc } from '../services/admin-platform-maintenance';

type Bindings = {
  DB: any;
  RATE_LIMIT_KV: any;
  SESSION_KV: any;
  AI: any;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /windows — list all maintenance windows
app.get('/windows', async (c) => {
  try {
    const result = await svc.listWindows(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    const windows = result.data as unknown[];
    return c.json({ windows, count: windows.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /windows — create a new maintenance window
app.post('/windows', async (c) => {
  try {
    const body = await c.req.json<{
      title?: string;
      description?: string;
      scheduled_start?: string;
      scheduled_end?: string;
      status?: string;
      affected_services?: string;
    }>();

    if (!body.title?.trim()) {
      return c.json({ error: 'title is required' }, 400);
    }
    if (!body.scheduled_start?.trim()) {
      return c.json({ error: 'scheduled_start is required' }, 400);
    }
    if (!body.scheduled_end?.trim()) {
      return c.json({ error: 'scheduled_end is required' }, 400);
    }

    const result = await svc.createWindow(c.env.DB, {
      title: body.title.trim(),
      description: body.description,
      scheduled_start: body.scheduled_start.trim(),
      scheduled_end: body.scheduled_end.trim(),
      status: body.status,
      affected_services: body.affected_services,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /notifications — list all maintenance notifications
app.get('/notifications', async (c) => {
  try {
    const result = await svc.getNotifications(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    const notifications = result.data as unknown[];
    return c.json({ notifications, count: notifications.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregated maintenance stats
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminPlatformMaintenance };
