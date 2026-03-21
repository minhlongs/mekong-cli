/**
 * Platform Health Dashboard routes — aggregated system status endpoints
 * Public: /overview, /services, /degraded, /features, /endpoints
 * Admin (X-Admin-Key): /capacity, /history, /snapshot, /services/:name
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import {
  checkServiceHealth,
  getPlatformOverview,
  getDegradedServices,
  getServiceStatuses,
  updateServiceStatus,
  getSystemCapacity,
} from '../services/platform-health-service';
import { getFeatureCoverage, getApiEndpointCount } from '../services/platform-feature-registry';
import { takeHealthSnapshot, getHealthHistory } from '../services/platform-health-snapshot-service';

export const app = new Hono<{ Bindings: Env }>();

// Admin auth middleware
const requireAdminKey = async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
};

// GET /platform-health/overview — public aggregated overview
app.get('/overview', async (c) => {
  try {
    const overview = await getPlatformOverview(c.env.DB);
    return c.json({ ok: true, data: overview });
  } catch (err) {
    return c.json({ error: 'Failed to fetch overview', details: String(err) }, 500);
  }
});

// GET /platform-health/services — public list all service statuses
app.get('/services', async (c) => {
  try {
    // Run live check + return persisted statuses
    const [live, stored] = await Promise.all([
      checkServiceHealth(c.env.DB),
      getServiceStatuses(c.env.DB),
    ]);
    return c.json({ ok: true, live_checks: live, stored_statuses: stored });
  } catch (err) {
    return c.json({ error: 'Failed to fetch services', details: String(err) }, 500);
  }
});

// GET /platform-health/degraded — public list degraded/down services
app.get('/degraded', async (c) => {
  try {
    const degraded = await getDegradedServices(c.env.DB);
    return c.json({ ok: true, count: degraded.length, data: degraded });
  } catch (err) {
    return c.json({ error: 'Failed to fetch degraded services', details: String(err) }, 500);
  }
});

// GET /platform-health/features — public feature coverage list
app.get('/features', (c) => {
  const coverage = getFeatureCoverage();
  return c.json({ ok: true, data: coverage });
});

// GET /platform-health/endpoints — public endpoint count
app.get('/endpoints', (c) => {
  return c.json({ ok: true, data: getApiEndpointCount() });
});

// --- Admin routes below ---

// GET /platform-health/capacity — D1 row counts (admin)
app.get('/capacity', requireAdminKey, async (c) => {
  try {
    const capacity = await getSystemCapacity(c.env.DB);
    return c.json({ ok: true, data: capacity });
  } catch (err) {
    return c.json({ error: 'Failed to fetch capacity', details: String(err) }, 500);
  }
});

// GET /platform-health/history — snapshot history (admin)
app.get('/history', requireAdminKey, async (c) => {
  try {
    const days = parseInt(c.req.query('days') ?? '7', 10);
    const safeDays = Math.min(Math.max(1, days), 90);
    const history = await getHealthHistory(c.env.DB, safeDays);
    return c.json({ ok: true, days: safeDays, count: history.length, data: history });
  } catch (err) {
    return c.json({ error: 'Failed to fetch history', details: String(err) }, 500);
  }
});

// POST /platform-health/snapshot — trigger health snapshot (admin)
app.post('/snapshot', requireAdminKey, async (c) => {
  try {
    const snapshot = await takeHealthSnapshot(c.env.DB);
    return c.json({ ok: true, data: snapshot }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to take snapshot', details: String(err) }, 500);
  }
});

// PUT /platform-health/services/:name — update a service status (admin)
app.put('/services/:name', requireAdminKey, async (c) => {
  try {
    const name = c.req.param('name');
    const body = await c.req.json().catch(() => ({}));
    const { status, response_time_ms, error_message } = body as {
      status?: string;
      response_time_ms?: number;
      error_message?: string;
    };

    const validStatuses = ['operational', 'degraded', 'down'];
    if (!status || !validStatuses.includes(status)) {
      return c.json({ error: 'Invalid status. Must be: operational | degraded | down' }, 400);
    }

    await updateServiceStatus(
      c.env.DB,
      name,
      status as 'operational' | 'degraded' | 'down',
      response_time_ms ?? 0,
      error_message,
    );

    return c.json({ ok: true, service: name, status });
  } catch (err) {
    return c.json({ error: 'Failed to update service status', details: String(err) }, 500);
  }
});

export { app as platformHealth };
