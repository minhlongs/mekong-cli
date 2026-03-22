/**
 * API Usage Analytics routes — per-endpoint stats, latency percentiles, error breakdown
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getUsageSummary,
  getEndpointStats,
  getTopEndpoints,
  getSlowestEndpoints,
  getErrorBreakdown,
  getErrorHotspots,
  getLatencyTrend,
  getRequestVolumeTrend,
  recordRequest,
  recordError,
} from '../services/api-usage-analytics-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/*', auth());

/** GET /v1/api-analytics/summary */
app.get('/summary', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await getUsageSummary(c.env.DB, tenantId);
    return json(data);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/endpoints?days=7 */
app.get('/endpoints', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const days = parseInt(c.req.query('days') ?? '7', 10);
    const data = await getEndpointStats(c.env.DB, tenantId, days);
    return json({ endpoints: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/top?limit=10 */
app.get('/top', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '10', 10);
    const data = await getTopEndpoints(c.env.DB, tenantId, limit);
    return json({ endpoints: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/slowest?limit=10 */
app.get('/slowest', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '10', 10);
    const data = await getSlowestEndpoints(c.env.DB, tenantId, limit);
    return json({ endpoints: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/errors?endpoint=... */
app.get('/errors', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const endpoint = c.req.query('endpoint');
    const data = await getErrorBreakdown(c.env.DB, tenantId, endpoint);
    return json({ errors: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/errors/hotspots */
app.get('/errors/hotspots', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await getErrorHotspots(c.env.DB, tenantId);
    return json({ hotspots: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/trend/latency?endpoint=...&days=14 */
app.get('/trend/latency', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const endpoint = c.req.query('endpoint') ?? '';
    const days = parseInt(c.req.query('days') ?? '14', 10);
    if (!endpoint) return json({ error: 'endpoint query param required' }, { status: 400 });
    const data = await getLatencyTrend(c.env.DB, tenantId, endpoint, days);
    return json({ trend: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /v1/api-analytics/trend/volume?days=14 */
app.get('/trend/volume', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const days = parseInt(c.req.query('days') ?? '14', 10);
    const data = await getRequestVolumeTrend(c.env.DB, tenantId, days);
    return json({ trend: data });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /v1/api-analytics/record — manual/test recording */
app.post('/record', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({}));
    const { endpoint, method, status_code, latency_ms, error_message } = body;

    if (!endpoint || !method || !status_code || latency_ms == null) {
      return json({ error: 'endpoint, method, status_code, latency_ms required' }, { status: 400 });
    }

    await recordRequest(c.env.DB, tenantId, endpoint, method, status_code, latency_ms);

    if (status_code >= 400) {
      await recordError(c.env.DB, tenantId, endpoint, method, status_code, error_message);
    }

    return json({ success: true });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

export { app as apiUsageAnalytics };
