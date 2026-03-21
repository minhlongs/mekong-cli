/**
 * Usage Forecasting routes — ML-lite capacity planning predictions
 *
 * Tenant routes require auth middleware.
 * Admin routes require X-Admin-Key header.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  recordSnapshot,
  getSnapshots,
  generateForecast,
  getForecast,
  getAllForecasts,
  detectAnomalies,
  getCapacityAlert,
  collectDailySnapshots,
} from '../services/usage-forecast-service';
import type { MetricType, ModelType } from '../services/usage-forecast-service';

const app = new Hono<{ Bindings: Env }>();

// All tenant routes require auth
app.use('/*', auth());

/**
 * GET /snapshots — historical usage snapshots
 * Query: ?metric=missions&days=30
 */
app.get('/snapshots', async (c) => {
  const { tenantId } = getTenant(c);
  const metric = (c.req.query('metric') ?? 'missions') as MetricType;
  const days = Math.min(parseInt(c.req.query('days') ?? '30', 10) || 30, 90);
  const data = await getSnapshots(c.env.DB, tenantId, metric, days);
  return json({ metric, days, snapshots: data });
});

/**
 * POST /snapshots — record a usage snapshot manually
 * Body: { metric_type, value, date? }
 */
app.post('/snapshots', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{ metric_type: MetricType; value: number; date?: string }>();
  if (!body.metric_type || body.value == null) {
    return json({ error: 'metric_type and value are required' }, { status: 400 });
  }
  await recordSnapshot(c.env.DB, tenantId, body.metric_type, body.value, body.date);
  return json({ recorded: true, metric_type: body.metric_type, value: body.value });
});

/**
 * POST /generate — generate forecast for a metric
 * Body: { metric_type, days_ahead?, model_type? }
 */
app.post('/generate', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{
    metric_type: MetricType;
    days_ahead?: number;
    model_type?: ModelType;
  }>();
  if (!body.metric_type) {
    return json({ error: 'metric_type is required' }, { status: 400 });
  }
  const daysAhead = Math.min(body.days_ahead ?? 7, 30);
  const modelType = body.model_type ?? 'linear';
  const forecasts = await generateForecast(c.env.DB, tenantId, body.metric_type, daysAhead, modelType);
  return json({ metric_type: body.metric_type, model_type: modelType, forecasts });
});

/**
 * GET /forecast — latest forecast for a metric
 * Query: ?metric=missions
 */
app.get('/forecast', async (c) => {
  const { tenantId } = getTenant(c);
  const metric = (c.req.query('metric') ?? 'missions') as MetricType;
  const forecasts = await getForecast(c.env.DB, tenantId, metric);
  return json({ metric, forecasts });
});

/**
 * GET /all — latest forecasts for all metric types
 */
app.get('/all', async (c) => {
  const { tenantId } = getTenant(c);
  const forecasts = await getAllForecasts(c.env.DB, tenantId);
  return json({ forecasts });
});

/**
 * GET /anomalies — detect anomalies in usage history
 * Query: ?metric=missions
 */
app.get('/anomalies', async (c) => {
  const { tenantId } = getTenant(c);
  const metric = (c.req.query('metric') ?? 'missions') as MetricType;
  const anomalies = await detectAnomalies(c.env.DB, tenantId, metric);
  return json({ metric, anomaly_count: anomalies.length, anomalies });
});

/**
 * GET /capacity-alert — check if forecasts approach/exceed plan limits
 */
app.get('/capacity-alert', async (c) => {
  const { tenantId } = getTenant(c);
  const alerts = await getCapacityAlert(c.env.DB, tenantId);
  return json({ alert_count: alerts.length, alerts });
});

// ─── Admin routes ────────────────────────────────────────────────────────────

/**
 * POST /admin/collect-all — collect daily snapshots for all active tenants
 * Requires X-Admin-Key header
 */
app.post('/admin/collect-all', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin key required' }, { status: 403 });
  }

  const rows = await c.env.DB
    .prepare(`SELECT id FROM tenants WHERE suspended_at IS NULL LIMIT 500`)
    .all<{ id: string }>();

  const tenants = rows.results ?? [];
  let collected = 0;
  const errors: string[] = [];

  for (const { id } of tenants) {
    try {
      await collectDailySnapshots(c.env.DB, id);
      collected++;
    } catch (err) {
      errors.push(`${id}: ${(err as Error).message}`);
    }
  }

  return json({ collected, total: tenants.length, errors });
});

export { app as usageForecasting };
