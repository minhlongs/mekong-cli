/**
 * Platform Cost Dashboard routes — admin-only
 * All endpoints require X-Admin-Key header matching ADMIN_API_KEY env var.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformCostDashboardService as svc } from '../services/platform-cost-dashboard-service';

export const platformCostDashboard = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

/** GET /entries — list cost entries, optional ?category=&period= filters */
platformCostDashboard.get('/entries', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const category = c.req.query('category');
    const period = c.req.query('period');
    const entries = await svc.listEntries(c.env.DB, { category, period });
    return c.json({ entries, count: entries.length });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** POST /entries — record a new cost entry */
platformCostDashboard.post('/entries', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const body = await c.req.json().catch(() => ({}));
    if (!body.category)     return c.json({ error: 'category is required' }, 400);
    if (!body.provider)     return c.json({ error: 'provider is required' }, 400);
    if (!body.service_name) return c.json({ error: 'service_name is required' }, 400);
    if (typeof body.amount !== 'number') return c.json({ error: 'amount must be a number' }, 400);
    const entry = await svc.createEntry(c.env.DB, body);
    return c.json({ entry }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /budgets — list monthly budgets, optional ?period= filter */
platformCostDashboard.get('/budgets', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const period = c.req.query('period');
    const budgets = await svc.getBudgets(c.env.DB, period);
    return c.json({ budgets });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /dashboard — aggregated spend summary vs budgets, optional ?period= */
platformCostDashboard.get('/dashboard', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const period = c.req.query('period');
    const dashboard = await svc.getDashboard(c.env.DB, period);
    return c.json(dashboard);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});
