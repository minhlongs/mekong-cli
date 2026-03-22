/**
 * Mission Execution Metrics routes
 * Auth: GET /metrics, POST /metrics, GET /aggregates
 * Admin: GET /admin/overview (X-Admin-Key, 403 on mismatch)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionExecutionMetricsService } from '../services/mission-execution-metrics-service';

const app = new Hono<{ Bindings: Env }>();

// --- Authenticated tenant routes ---

app.use('/metrics', auth());
app.use('/aggregates', auth());

/** GET /metrics — List execution metrics for authenticated tenant */
app.get('/metrics', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const missionId = c.req.query('mission_id')?.trim() || undefined;
    const metrics = await missionExecutionMetricsService.listMetrics(c.env.DB, tenantId, missionId);
    return c.json({ success: true, data: metrics, total: metrics.length });
  } catch (err) {
    console.error('[missionExecutionMetrics GET /metrics] error:', err);
    return c.json({ error: 'Failed to list metrics' }, 500);
  }
});

/** POST /metrics — Record a mission execution metric */
app.post('/metrics', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    const missionId = (body.mission_id ?? '').trim();
    if (!missionId) {
      return c.json({ error: 'mission_id is required' }, 400);
    }

    const executionTimeMs = Number(body.execution_time_ms);
    if (!Number.isFinite(executionTimeMs) || executionTimeMs < 0) {
      return c.json({ error: 'execution_time_ms must be a non-negative number' }, 400);
    }

    const metric = await missionExecutionMetricsService.recordMetric(c.env.DB, tenantId, {
      missionId,
      executionTimeMs,
      tokensUsed: body.tokens_used ?? 0,
      modelUsed: body.model_used ?? undefined,
      success: body.success ?? 1,
      errorType: body.error_type ?? undefined,
    });
    return c.json({ success: true, data: metric }, 201);
  } catch (err) {
    console.error('[missionExecutionMetrics POST /metrics] error:', err);
    return c.json({ error: 'Failed to record metric' }, 500);
  }
});

/** GET /aggregates — Get execution aggregates for authenticated tenant */
app.get('/aggregates', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const aggregates = await missionExecutionMetricsService.getAggregates(c.env.DB, tenantId);
    return c.json({ success: true, data: aggregates, total: aggregates.length });
  } catch (err) {
    console.error('[missionExecutionMetrics GET /aggregates] error:', err);
    return c.json({ error: 'Failed to fetch aggregates' }, 500);
  }
});

// --- Admin routes ---

/** GET /admin/overview — Platform-wide execution stats across all tenants */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const overview = await missionExecutionMetricsService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview, total: overview.length });
  } catch (err) {
    console.error('[missionExecutionMetrics GET /admin/overview] error:', err);
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as missionExecutionMetrics };
