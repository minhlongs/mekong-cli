/**
 * Feature Flags routes — admin CRUD + tenant evaluation endpoints
 * Admin:  GET / POST /:key PUT /:key DELETE /:key PUT /:key/override/:tenantId DELETE /:key/override/:tenantId GET /:key/stats
 * JWT:    GET /evaluate  GET /evaluate/:key
 *
 * IMPORTANT: /evaluate routes mounted BEFORE /:key to avoid shadowing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createFlag,
  getFlags,
  getFlag,
  updateFlag,
  deleteFlag,
  evaluateFlag,
  evaluateAllFlags,
  setTenantOverride,
  removeTenantOverride,
  getFlagStats,
} from '../services/feature-flag-service';

const app = new Hono<{ Bindings: Env }>();

/** Returns true when request carries valid admin key */
function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── JWT: evaluate all enabled flags for the authenticated tenant ──────────────
app.get('/evaluate', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const flags = await evaluateAllFlags(c.env.DB, tenantId);
  return c.json({ success: true, data: { tenant_id: tenantId, flags } });
});

// ── JWT: evaluate a single flag for the authenticated tenant ──────────────────
app.get('/evaluate/:key', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const key = c.req.param('key');
  const flag = await getFlag(c.env.DB, key);
  if (!flag) return c.json({ success: false, error: 'Flag not found' }, 404);
  const result = await evaluateFlag(c.env.DB, key, tenantId);
  return c.json({ success: true, data: { flag_key: key, tenant_id: tenantId, result } });
});

// ── Admin: list all flags ─────────────────────────────────────────────────────
app.get('/', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const flags = await getFlags(c.env.DB);
  return c.json({ success: true, data: flags });
});

// ── Admin: create flag ────────────────────────────────────────────────────────
app.post('/', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const body = await c.req.json<{
    key: string; name: string; description?: string;
    flagType?: string; defaultValue?: string;
    enabled?: boolean; rolloutPercentage?: number; variants?: unknown[];
  }>();
  if (!body.key || !body.name) {
    return c.json({ success: false, error: 'key and name are required' }, 400);
  }
  try {
    const flag = await createFlag(c.env.DB, body as Parameters<typeof createFlag>[1]);
    return c.json({ success: true, data: flag }, 201);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to create flag';
    return c.json({ success: false, error: msg }, 409);
  }
});

// ── Admin: get flag details ───────────────────────────────────────────────────
app.get('/:key', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const flag = await getFlag(c.env.DB, c.req.param('key'));
  if (!flag) return c.json({ success: false, error: 'Flag not found' }, 404);
  return c.json({ success: true, data: flag });
});

// ── Admin: update flag ────────────────────────────────────────────────────────
app.put('/:key', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const key = c.req.param('key');
  const body = await c.req.json();
  const flag = await updateFlag(c.env.DB, key, body);
  if (!flag) return c.json({ success: false, error: 'Flag not found' }, 404);
  return c.json({ success: true, data: flag });
});

// ── Admin: delete flag ────────────────────────────────────────────────────────
app.delete('/:key', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const deleted = await deleteFlag(c.env.DB, c.req.param('key'));
  if (!deleted) return c.json({ success: false, error: 'Flag not found' }, 404);
  return c.json({ success: true, data: { deleted: true } });
});

// ── Admin: set per-tenant override ───────────────────────────────────────────
app.put('/:key/override/:tenantId', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const { key, tenantId } = c.req.param();
  const { value } = await c.req.json<{ value: string }>();
  if (value === undefined) return c.json({ success: false, error: 'value is required' }, 400);
  try {
    await setTenantOverride(c.env.DB, key, tenantId, String(value));
    return c.json({ success: true, data: { flag_key: key, tenant_id: tenantId, value } });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to set override';
    return c.json({ success: false, error: msg }, 404);
  }
});

// ── Admin: remove per-tenant override ────────────────────────────────────────
app.delete('/:key/override/:tenantId', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const { key, tenantId } = c.req.param();
  try {
    await removeTenantOverride(c.env.DB, key, tenantId);
    return c.json({ success: true, data: { flag_key: key, tenant_id: tenantId, removed: true } });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to remove override';
    return c.json({ success: false, error: msg }, 404);
  }
});

// ── Admin: evaluation stats ───────────────────────────────────────────────────
app.get('/:key/stats', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  const key = c.req.param('key');
  const flag = await getFlag(c.env.DB, key);
  if (!flag) return c.json({ success: false, error: 'Flag not found' }, 404);
  const stats = await getFlagStats(c.env.DB, key);
  return c.json({ success: true, data: { flag_key: key, ...stats } });
});

export const featureFlags = app;
