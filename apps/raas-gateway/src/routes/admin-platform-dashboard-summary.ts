/**
 * Admin Platform Dashboard Summary Routes
 * Widget management + live dashboard aggregation + snapshot history
 * All endpoints protected by X-Admin-Key header (403 on failure)
 */

import { Hono } from 'hono';
import { adminPlatformDashboardSummaryService } from '../services/admin-platform-dashboard-summary';

const app = new Hono<{ Bindings: { DB: any; ADMIN_API_KEY: string } }>();

// Admin auth guard — 403 on missing/invalid key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /admin/dashboard-summary/widgets — list all configured widgets
app.get('/widgets', async (c) => {
  try {
    const result = await adminPlatformDashboardSummaryService.listWidgets(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// POST /admin/dashboard-summary/widgets — create a new dashboard widget
app.post('/widgets', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.widget_name || !body.data_source) {
      return c.json({ error: 'widget_name and data_source are required' }, 400);
    }
    const result = await adminPlatformDashboardSummaryService.createWidget(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /admin/dashboard-summary/snapshots?limit=30 — list historical snapshots
app.get('/snapshots', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') ?? '30', 10);
    const result = await adminPlatformDashboardSummaryService.getSnapshots(c.env.DB, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /admin/dashboard-summary/dashboard — live aggregate + persist snapshot
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformDashboardSummaryService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

export { app as adminPlatformDashboardSummary };
