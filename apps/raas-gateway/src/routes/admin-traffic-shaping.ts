/**
 * Admin Traffic Shaping routes — manage rate rules, view events, dashboard stats
 * All endpoints require X-Admin-Key header. Mount path: /admin/traffic-shaping
 */

import { Hono } from 'hono';
import { adminTrafficShapingService as svc } from '../services/admin-traffic-shaping';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth check on ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /rules — list all traffic rules ordered by priority
app.get('/rules', async (c) => {
  try {
    const rules = await svc.listRules(c.env.DB);
    return c.json({ rules, count: rules.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /rules — create a new traffic rule
app.post('/rules', async (c) => {
  try {
    const body = await c.req.json<{
      rule_name: string;
      target_pattern: string;
      max_rps: number;
      burst_size?: number;
      priority?: number;
      is_active?: number;
    }>();
    if (!body.rule_name || !body.target_pattern || body.max_rps === undefined) {
      return c.json({ error: 'rule_name, target_pattern, and max_rps are required' }, 400);
    }
    const rule = await svc.createRule(c.env.DB, body);
    return c.json(rule, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /events — list recent traffic events (last 500)
app.get('/events', async (c) => {
  try {
    const events = await svc.getEvents(c.env.DB);
    return c.json({ events, count: events.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregated traffic shaping stats
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminTrafficShaping };
