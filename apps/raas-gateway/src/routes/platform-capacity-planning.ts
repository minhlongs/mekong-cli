/**
 * Platform Capacity Planning routes — capacity snapshots, forecasts, scaling recommendations
 * All endpoints are admin-only (X-Admin-Key). Mount path: /admin/capacity
 */

import { Hono } from 'hono';
import * as svc from '../services/platform-capacity-planning-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware — all capacity planning routes require X-Admin-Key
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// POST /snapshots — record a capacity snapshot
app.post('/snapshots', async (c) => {
  try {
    const body = await c.req.json<{ resource_type: svc.ResourceType; current_usage: number; max_capacity: number }>();
    if (!body.resource_type || body.current_usage == null || body.max_capacity == null) {
      return c.json({ error: 'resource_type, current_usage, max_capacity required' }, 400);
    }
    const snapshot = await svc.recordSnapshot(c.env.DB, body);
    return c.json({ success: true, data: snapshot }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /snapshots — list snapshots (optional ?resource_type= &limit=)
app.get('/snapshots', async (c) => {
  try {
    const resourceType = c.req.query('resource_type') as svc.ResourceType | undefined;
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const snapshots = await svc.getSnapshots(c.env.DB, resourceType, limit);
    return c.json({ success: true, data: snapshots, count: snapshots.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /current — latest snapshot per resource type
app.get('/current', async (c) => {
  try {
    const result = await svc.getCurrentCapacity(c.env.DB);
    return c.json({ success: true, data: result });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /forecasts — create a capacity forecast
app.post('/forecasts', async (c) => {
  try {
    const body = await c.req.json<{ resource_type: svc.ResourceType; forecast_date: string; predicted_usage: number; confidence_pct: number; model_version?: string }>();
    if (!body.resource_type || !body.forecast_date || body.predicted_usage == null || body.confidence_pct == null) {
      return c.json({ error: 'resource_type, forecast_date, predicted_usage, confidence_pct required' }, 400);
    }
    const forecast = await svc.createForecast(c.env.DB, body);
    return c.json({ success: true, data: forecast }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /forecasts — list forecasts (optional ?resource_type=)
app.get('/forecasts', async (c) => {
  try {
    const resourceType = c.req.query('resource_type') as svc.ResourceType | undefined;
    const forecasts = await svc.getForecasts(c.env.DB, resourceType);
    return c.json({ success: true, data: forecasts, count: forecasts.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /recommendations — create a scaling recommendation
app.post('/recommendations', async (c) => {
  try {
    const body = await c.req.json<{ resource_type: svc.ResourceType; recommendation_type: svc.RecommendationType; current_value: number; recommended_value: number; reason: string; priority?: svc.Priority }>();
    if (!body.resource_type || !body.recommendation_type || body.current_value == null || body.recommended_value == null || !body.reason) {
      return c.json({ error: 'resource_type, recommendation_type, current_value, recommended_value, reason required' }, 400);
    }
    const rec = await svc.createRecommendation(c.env.DB, body);
    return c.json({ success: true, data: rec }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /recommendations — list recommendations (optional ?status=)
app.get('/recommendations', async (c) => {
  try {
    const status = c.req.query('status') as svc.RecommendationStatus | undefined;
    const recs = await svc.listRecommendations(c.env.DB, status);
    return c.json({ success: true, data: recs, count: recs.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /recommendations/:id — update recommendation status
app.put('/recommendations/:id', async (c) => {
  try {
    const body = await c.req.json<{ status: svc.RecommendationStatus }>();
    if (!body.status) return c.json({ error: 'status required' }, 400);
    const rec = await svc.updateRecommendation(c.env.DB, c.req.param('id'), body.status);
    if (!rec) return c.json({ error: 'Recommendation not found' }, 404);
    return c.json({ success: true, data: rec });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — full capacity planning dashboard
app.get('/dashboard', async (c) => {
  try {
    const data = await svc.getCapacityDashboard(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformCapacityPlanning };
