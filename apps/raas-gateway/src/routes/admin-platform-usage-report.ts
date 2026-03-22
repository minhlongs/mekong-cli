/**
 * Admin platform usage report routes
 * All endpoints require X-Admin-Key header — returns 403 if missing or invalid
 *
 * GET  /reports    — list all reports
 * POST /reports    — create a new report
 * GET  /sections   — get sections for a report (?report_id=)
 * GET  /dashboard  — aggregate dashboard stats
 */

import { Hono } from 'hono';
import { adminPlatformUsageReportService } from '../services/admin-platform-usage-report';

// Inline Bindings — avoids importing from index.ts
type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-key guard for all routes
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /reports — list all platform usage reports
app.get('/reports', async (c) => {
  try {
    const result = await adminPlatformUsageReportService.listReports(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

// POST /reports — create a new platform usage report
app.post('/reports', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.id || !body.report_name || !body.period) {
      return c.json({ error: 'id, report_name, and period are required' }, 400);
    }
    const result = await adminPlatformUsageReportService.createReport(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

// GET /sections — get sections for a report (?report_id=<id>)
app.get('/sections', async (c) => {
  try {
    const reportId = c.req.query('report_id');
    if (!reportId) {
      return c.json({ error: 'report_id query param is required' }, 400);
    }
    const result = await adminPlatformUsageReportService.getSections(c.env.DB, reportId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

// GET /dashboard — platform-wide aggregate stats
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformUsageReportService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

export { app as adminPlatformUsageReport };
