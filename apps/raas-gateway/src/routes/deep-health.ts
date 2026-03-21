/**
 * Deep Health routes — dependency-aware health checks with latency tracking
 * Mount at: /health/deep
 * Public endpoints (no auth) except /history (admin only)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  checkD1Health,
  checkKVHealth,
  getHealthHistory,
  recordHealthSnapshot,
  runFullHealthCheck,
} from '../services/deep-health-service';

export const deepHealth = new Hono<{ Bindings: Env }>();

/**
 * GET /health/deep — full dependency health check (public, no auth)
 * Runs all checks in parallel and records snapshot
 */
deepHealth.get('/', async (c) => {
  try {
    const result = await runFullHealthCheck(c.env);
    // Fire-and-forget snapshot — do not block response
    c.executionCtx?.waitUntil(recordHealthSnapshot(c.env.DB, result));
    const status = result.status === 'healthy' ? 200 : result.status === 'degraded' ? 207 : 503;
    return json(result, { status });
  } catch (err) {
    return json({ error: 'Health check failed', code: 'HEALTH_CHECK_ERROR' }, { status: 500 });
  }
});

/**
 * GET /health/deep/d1 — D1 database health only (public)
 */
deepHealth.get('/d1', async (c) => {
  try {
    const check = await checkD1Health(c.env.DB);
    const status = check.status === 'healthy' ? 200 : check.status === 'degraded' ? 207 : 503;
    return json({ success: true, data: check }, { status });
  } catch (err) {
    return json({ error: 'D1 health check failed', code: 'D1_HEALTH_ERROR' }, { status: 500 });
  }
});

/**
 * GET /health/deep/kv — KV store health only (public)
 */
deepHealth.get('/kv', async (c) => {
  try {
    const check = await checkKVHealth(c.env.RATE_LIMIT_KV);
    const status = check.status === 'healthy' ? 200 : check.status === 'degraded' ? 207 : 503;
    return json({ success: true, data: check }, { status });
  } catch (err) {
    return json({ error: 'KV health check failed', code: 'KV_HEALTH_ERROR' }, { status: 500 });
  }
});

/**
 * GET /health/deep/history — historical health snapshots (admin only via X-Admin-Key)
 * Query: ?limit=24
 */
deepHealth.get('/history', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin access required', code: 'FORBIDDEN' }, { status: 403 });
  }

  try {
    const limit = Math.min(parseInt(c.req.query('limit') ?? '24', 10) || 24, 100);
    const history = await getHealthHistory(c.env.DB, limit);
    return json({ success: true, data: history });
  } catch (err) {
    return json({ error: 'Failed to fetch health history', code: 'HEALTH_HISTORY_ERROR' }, { status: 500 });
  }
});
