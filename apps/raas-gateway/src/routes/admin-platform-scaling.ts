/**
 * Admin Platform Scaling routes — scaling rules CRUD and event history
 * All endpoints protected by X-Admin-Key header check
 * Mounted at /admin/platform-scaling in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminPlatformScalingService as svc } from '../services/admin-platform-scaling-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /rules — list scaling rules; ?active=1 to filter active only
app.get('/rules', async (c) => {
  try {
    const activeOnly = c.req.query('active') === '1';
    const result = await svc.listRules(c.env.DB, activeOnly);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /rules — create a new scaling rule
app.post('/rules', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.rule_name || !body.metric_trigger || body.threshold === undefined) {
      return c.json({ error: 'rule_name, metric_trigger, and threshold are required' }, 400);
    }
    const rule = await svc.createRule(c.env.DB, body);
    return c.json(rule, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /events — list scaling events; ?rule_id=&status=&limit= filters
app.get('/events', async (c) => {
  try {
    const rule_id = c.req.query('rule_id');
    const status = c.req.query('status');
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : undefined;
    const result = await svc.getEvents(c.env.DB, { rule_id, status, limit });
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /dashboard — active rules count, direction breakdown, recent events
app.get('/dashboard', async (c) => {
  try {
    const data = await svc.getDashboard(c.env.DB);
    return c.json(data);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminPlatformScaling };
