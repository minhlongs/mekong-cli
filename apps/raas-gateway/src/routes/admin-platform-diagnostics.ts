/**
 * Admin Platform Diagnostics Routes
 * Protected by X-Admin-Key — returns platform health checks and aggregated reports
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminPlatformDiagnosticsService as svc } from '../services/admin-platform-diagnostics-service';

export const adminPlatformDiagnostics = new Hono<{ Bindings: Env }>();

// Admin-only guard — all routes require X-Admin-Key
adminPlatformDiagnostics.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /checks — list recent diagnostic check records
adminPlatformDiagnostics.get('/checks', async (c) => {
  try {
    const checks = await svc.listChecks(c.env.DB);
    return c.json({ checks });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

// POST /checks — run a named diagnostic check on demand
adminPlatformDiagnostics.post('/checks', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const name = body.check_name ?? 'manual_check';
    const type = body.check_type ?? 'health';
    const target = body.target ?? null;
    const check = await svc.runCheck(c.env.DB, name, type, target);
    return c.json({ check }, 201);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

// GET /reports — list aggregated diagnostic reports
adminPlatformDiagnostics.get('/reports', async (c) => {
  try {
    const reports = await svc.getReports(c.env.DB);
    return c.json({ reports });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

// GET /dashboard — run all built-in checks, persist report, return summary
adminPlatformDiagnostics.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});
