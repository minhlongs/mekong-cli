/**
 * Platform Error Budget routes — cross-service SLO budget tracking and dashboard
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-error-budget
 */

import { Hono } from 'hono';
import { platformErrorBudgetService as svc } from '../services/platform-error-budget';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /budgets — list all error budgets
app.get('/budgets', async (c) => {
  try {
    const budgets = await svc.listBudgets(c.env.DB);
    return c.json({ budgets, count: (budgets as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /budgets — create a new error budget
app.post('/budgets', async (c) => {
  try {
    const body = await c.req.json<{
      service_name: string;
      slo_target?: number;
      budget_remaining?: number;
      window_days?: number;
    }>();
    if (!body.service_name) {
      return c.json({ error: 'service_name is required' }, 400);
    }
    const budget = await svc.createBudget(c.env.DB, body);
    return c.json(budget, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /events — list events for a budget (query param: budget_id)
app.get('/events', async (c) => {
  try {
    const budgetId = c.req.query('budget_id');
    if (!budgetId) {
      return c.json({ error: 'budget_id query param is required' }, 400);
    }
    const events = await svc.getEvents(c.env.DB, budgetId);
    return c.json({ events, count: (events as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregate stats across all budgets
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformErrorBudget };
