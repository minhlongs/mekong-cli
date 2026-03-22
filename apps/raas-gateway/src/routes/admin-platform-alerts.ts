/**
 * Admin Platform Alerts routes — alert rule management and incident visibility
 * Admin-only: all routes require X-Admin-Key header matching ADMIN_API_KEY env var
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminPlatformAlertsService } from '../services/admin-platform-alerts-service';

export const adminPlatformAlerts = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

/** GET /rules — list all alert rules */
adminPlatformAlerts.get('/rules', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const rules = await adminPlatformAlertsService.listRules(c.env.DB);
    return c.json({ rules });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** POST /rules — create a new alert rule */
adminPlatformAlerts.post('/rules', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const body = await c.req.json().catch(() => ({}));
    if (!body.rule_name || !body.metric_name || !body.condition) {
      return c.json({ error: 'rule_name, metric_name, condition are required', code: 'INVALID_INPUT' }, 400);
    }
    const rule = await adminPlatformAlertsService.createRule(c.env.DB, body);
    return c.json({ rule }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /incidents — list incidents with optional ?rule_id=&status= filters */
adminPlatformAlerts.get('/incidents', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const rule_id = c.req.query('rule_id');
    const status = c.req.query('status');
    const incidents = await adminPlatformAlertsService.getIncidents(c.env.DB, { rule_id, status });
    return c.json({ incidents });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /dashboard — aggregated rule + incident summary */
adminPlatformAlerts.get('/dashboard', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const dashboard = await adminPlatformAlertsService.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});
