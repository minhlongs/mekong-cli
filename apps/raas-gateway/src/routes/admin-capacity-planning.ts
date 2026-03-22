/**
 * Admin Capacity Planning routes — resource capacity plans and alerts
 * All endpoints require X-Admin-Key header. Mount path: /admin/capacity-planning
 */

import { Hono } from 'hono';
import { adminCapacityPlanningService as svc } from '../services/admin-capacity-planning';

type Env = {
  Bindings: {
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
};

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /plans — list all capacity plans
app.get('/plans', async (c) => {
  try {
    const plans = await svc.listPlans(c.env.DB);
    return c.json({ plans, count: plans.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /plans — create a new capacity plan
app.post('/plans', async (c) => {
  try {
    const body = await c.req.json<{
      resource_type?: string;
      current_usage?: number;
      max_capacity?: number;
      forecast_usage?: number;
      forecast_date?: string;
      status?: string;
    }>();

    if (!body.resource_type?.trim()) {
      return c.json({ error: 'resource_type is required' }, 400);
    }
    if (body.current_usage === undefined || body.max_capacity === undefined) {
      return c.json({ error: 'current_usage and max_capacity are required' }, 400);
    }

    const plan = await svc.createPlan(c.env.DB, {
      resource_type: body.resource_type.trim(),
      current_usage: body.current_usage,
      max_capacity: body.max_capacity,
      forecast_usage: body.forecast_usage,
      forecast_date: body.forecast_date,
      status: body.status,
    });
    return c.json(plan, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /alerts — list all capacity alerts
app.get('/alerts', async (c) => {
  try {
    const alerts = await svc.getAlerts(c.env.DB);
    return c.json({ alerts, count: alerts.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregated capacity stats across all plans
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminCapacityPlanning };
