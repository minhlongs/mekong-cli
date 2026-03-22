/**
 * API Response Caching routes — all admin-only (X-Admin-Key required)
 *
 * GET  /rules                        — list cache rules
 * POST /rules                        — create cache rule
 * PUT  /rules/:id                    — update cache rule
 * DELETE /rules/:id                  — delete cache rule
 * GET  /entries/:cacheKey            — get cache entry
 * POST /invalidate/path              — invalidate by path pattern
 * POST /invalidate/tenant/:tenantId  — invalidate by tenant
 * POST /purge                        — purge expired entries
 * GET  /analytics                    — get analytics
 * POST /analytics                    — record analytics
 * GET  /dashboard                    — admin overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  listRules, createRule, updateRule, deleteRule,
  getCacheEntry, setCacheEntry, invalidateByPath, invalidateByTenant,
  purgeExpired, getAnalytics, recordAnalytics, getAdminOverview,
} from '../services/api-response-caching-service';

const app = new Hono<{ Bindings: Env }>();

// ── Admin guard middleware ────────────────────────────────────────────────────

app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized', code: 'ADMIN_REQUIRED' }, { status: 401 });
  }
  return next();
});

// ── Cache Rules ───────────────────────────────────────────────────────────────

/** GET /rules — list all cache rules */
app.get('/rules', async (c) => {
  try {
    const rules = await listRules(c.env.DB);
    return c.json({ success: true, data: rules });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /rules — create a cache rule */
app.post('/rules', async (c) => {
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.path_pattern) {
    return json({ error: 'path_pattern is required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const rule = await createRule(c.env.DB, body as any);
    return c.json({ success: true, data: rule }, 201);
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** PUT /rules/:id — update a cache rule */
app.put('/rules/:id', async (c) => {
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const rule = await updateRule(c.env.DB, id, body as any);
    return c.json({ success: true, data: rule });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'DB error';
    const status = msg === 'Cache rule not found' ? 404 : 500;
    return json({ error: msg, code: status === 404 ? 'NOT_FOUND' : 'DB_ERROR' }, { status });
  }
});

/** DELETE /rules/:id — delete a cache rule */
app.delete('/rules/:id', async (c) => {
  const id = c.req.param('id');
  try {
    await deleteRule(c.env.DB, id);
    return c.json({ success: true, data: { id, deleted: true } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ── Cache Entries ─────────────────────────────────────────────────────────────

/** GET /entries/:cacheKey — fetch a cache entry */
app.get('/entries/:cacheKey', async (c) => {
  const cacheKey = c.req.param('cacheKey');
  try {
    const entry = await getCacheEntry(c.env.DB, cacheKey);
    if (!entry) return json({ error: 'Cache entry not found or expired', code: 'NOT_FOUND' }, { status: 404 });
    return c.json({ success: true, data: entry });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ── Invalidation ──────────────────────────────────────────────────────────────

/** POST /invalidate/path — invalidate entries by path pattern */
app.post('/invalidate/path', async (c) => {
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  const pattern = body.pattern as string;
  if (!pattern) return json({ error: 'pattern is required', code: 'BAD_REQUEST' }, { status: 400 });
  try {
    const deleted = await invalidateByPath(c.env.DB, pattern);
    return c.json({ success: true, data: { pattern, deleted } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /invalidate/tenant/:tenantId — invalidate all entries for a tenant */
app.post('/invalidate/tenant/:tenantId', async (c) => {
  const tenantId = c.req.param('tenantId');
  try {
    const deleted = await invalidateByTenant(c.env.DB, tenantId);
    return c.json({ success: true, data: { tenant_id: tenantId, deleted } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /purge — remove all expired cache entries */
app.post('/purge', async (c) => {
  try {
    const purged = await purgeExpired(c.env.DB);
    return c.json({ success: true, data: { purged } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ── Analytics ─────────────────────────────────────────────────────────────────

/** GET /analytics — list analytics records, optional ?period= filter */
app.get('/analytics', async (c) => {
  const period = c.req.query('period');
  try {
    const rows = await getAnalytics(c.env.DB, period);
    return c.json({ success: true, data: rows });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** POST /analytics — record an analytics entry */
app.post('/analytics', async (c) => {
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.period) return json({ error: 'period is required', code: 'BAD_REQUEST' }, { status: 400 });
  try {
    const row = await recordAnalytics(c.env.DB, body as any);
    return c.json({ success: true, data: row }, 201);
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

/** GET /dashboard — admin overview of cache system */
app.get('/dashboard', async (c) => {
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

export { app as apiResponseCaching };
