/**
 * Admin Capacity Planning routes — resource utilization plans and recommendations
 * All endpoints require X-Admin-Key header. Mount path: /admin/capacity
 */

import { Hono } from 'hono';
import { adminCapacityPlanningService as svc } from '../services/admin-capacity-planning';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard: all routes require valid X-Admin-Key
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /plans — list capacity plans; optional ?resource_type= filter
app.get('/plans', async (c) => {
  try {
    const resourceType = c.req.query('resource_type');
    const result = await svc.listPlans(c.env.DB, resourceType);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /plans — create a new capacity plan
app.post('/plans', async (c) => {
  try {
    const body = await c.req.json();

    if (!body.plan_name?.trim()) return c.json({ error: 'plan_name is required' }, 400);
    if (!body.resource_type?.trim()) return c.json({ error: 'resource_type is required' }, 400);
    if (body.current_usage === undefined) return c.json({ error: 'current_usage is required' }, 400);
    if (body.max_capacity === undefined) return c.json({ error: 'max_capacity is required' }, 400);

    const result = await svc.createPlan(c.env.DB, {
      plan_name: body.plan_name.trim(),
      resource_type: body.resource_type.trim(),
      current_usage: Number(body.current_usage),
      max_capacity: Number(body.max_capacity),
      forecast_date: body.forecast_date,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /recommendations — list recommendations for a plan (?plan_id= required)
app.get('/recommendations', async (c) => {
  try {
    const planId = c.req.query('plan_id');
    if (!planId) return c.json({ error: 'plan_id query param is required' }, 400);

    const result = await svc.getRecommendations(c.env.DB, planId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /dashboard — aggregated utilization summary and pending recommendation counts
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminCapacityPlanning };
