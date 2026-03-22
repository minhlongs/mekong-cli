/**
 * Platform Rate Limit Analytics routes — event ingestion, abuse detection, throttle history
 *
 * Admin (X-Admin-Key):
 *   POST /events              — recordEvent
 *   GET  /abuse               — listAbuse
 *   POST /abuse               — createAbuse
 *   POST /abuse/:id/resolve   — resolveAbuse
 *   POST /snapshots           — recordThrottleSnapshot
 *   GET  /top-throttled       — getTopThrottled
 *   GET  /admin/overview      — getAdminOverview
 *
 * Tenant (auth):
 *   GET  /events              — getEvents
 *   GET  /history             — getThrottleHistory
 *   GET  /stats               — getTenantRateLimitStats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  recordEvent,
  getEvents,
  listAbuse,
  createAbuse,
  resolveAbuse,
  getThrottleHistory,
  recordThrottleSnapshot,
  getTopThrottled,
  getTenantRateLimitStats,
  getAdminOverview,
} from '../services/platform-rate-limit-analytics-service';

const app = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Admin: POST /events — record a rate limit event
// ---------------------------------------------------------------------------

app.post('/events', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.tenant_id || !body.endpoint) {
    return json({ error: 'tenant_id and endpoint required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    await recordEvent(c.env.DB, {
      tenant_id: body.tenant_id as string,
      endpoint: body.endpoint as string,
      ip_address: body.ip_address as string | undefined,
      action: (body.action as string) ?? 'throttled',
      remaining: body.remaining as number | undefined,
      limit_value: body.limit_value as number | undefined,
      window_seconds: body.window_seconds as number | undefined,
    });
    return c.json({ success: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Tenant: GET /events — list rate limit events for current tenant
// ---------------------------------------------------------------------------

app.get('/events', auth(), async (c) => {
  const tenant = getTenant(c);
  const endpoint = c.req.query('endpoint');
  const action = c.req.query('action');
  const limit = parseInt(c.req.query('limit') ?? '50', 10);
  try {
    const events = await getEvents(c.env.DB, tenant.tenantId, { endpoint, action, limit });
    return c.json({ success: true, data: events });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: GET /abuse — list abuse detections
// ---------------------------------------------------------------------------

app.get('/abuse', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  const filters = {
    ip_address: c.req.query('ip_address'),
    detection_type: c.req.query('detection_type'),
    severity: c.req.query('severity'),
    resolved: c.req.query('resolved') !== undefined ? parseInt(c.req.query('resolved')!, 10) : undefined,
  };
  try {
    const detections = await listAbuse(c.env.DB, filters);
    return c.json({ success: true, data: detections });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: POST /abuse — create abuse detection record
// ---------------------------------------------------------------------------

app.post('/abuse', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.ip_address) {
    return json({ error: 'ip_address required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const id = await createAbuse(c.env.DB, {
      tenant_id: body.tenant_id as string | undefined,
      ip_address: body.ip_address as string,
      detection_type: (body.detection_type as string) ?? 'brute_force',
      severity: (body.severity as string) ?? 'medium',
      details_json: body.details_json ? JSON.stringify(body.details_json) : '{}',
    });
    return c.json({ success: true, data: { id } }, 201);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: POST /abuse/:id/resolve — mark abuse detection as resolved
// ---------------------------------------------------------------------------

app.post('/abuse/:id/resolve', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  const id = c.req.param('id');
  try {
    await resolveAbuse(c.env.DB, id);
    return c.json({ success: true, data: { id, resolved: true } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Tenant: GET /history — throttle history for current tenant
// ---------------------------------------------------------------------------

app.get('/history', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const history = await getThrottleHistory(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: history });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: POST /snapshots — record throttle snapshot
// ---------------------------------------------------------------------------

app.post('/snapshots', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.tenant_id || !body.period) {
    return json({ error: 'tenant_id and period required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    await recordThrottleSnapshot(c.env.DB, body.tenant_id as string, {
      period: body.period as string,
      total_requests: (body.total_requests as number) ?? 0,
      throttled_requests: (body.throttled_requests as number) ?? 0,
      unique_ips: (body.unique_ips as number) ?? 0,
      top_endpoints_json: body.top_endpoints_json ? JSON.stringify(body.top_endpoints_json) : '[]',
    });
    return c.json({ success: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: GET /top-throttled — top throttled endpoints across platform
// ---------------------------------------------------------------------------

app.get('/top-throttled', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    const data = await getTopThrottled(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Tenant: GET /stats — rate limit stats for current tenant
// ---------------------------------------------------------------------------

app.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await getTenantRateLimitStats(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, ...stats } });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin: GET /admin/overview — platform-wide rate limit overview
// ---------------------------------------------------------------------------

app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return json({ error: message, code: 'DB_ERROR' }, { status: 500 });
  }
});

export { app as platformRateLimitAnalytics };
