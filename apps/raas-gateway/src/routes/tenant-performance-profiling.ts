/**
 * Tenant Performance Profiling Routes
 * Mount at: /v1/performance
 *
 * GET  /profiles        — list profiles for authenticated tenant
 * POST /profiles        — create a profile for authenticated tenant
 * GET  /baselines       — list baselines for authenticated tenant
 * GET  /admin/overview  — platform-wide overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import {
  listProfiles,
  createProfile,
  getBaselines,
  getAdminOverview,
  type CreateProfileInput,
} from '../services/tenant-performance-profiling';

// Inline Bindings — avoids coupling to Env import per spec
type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── GET /profiles ─────────────────────────────────────────────────────────────

app.get('/profiles', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const result = await listProfiles(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[performance GET /profiles]', err);
    return c.json({ error: 'Failed to list performance profiles' }, 500);
  }
});

// ── POST /profiles ────────────────────────────────────────────────────────────

app.post('/profiles', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<CreateProfileInput>();

    if (!body.profile_name || !body.endpoint) {
      return c.json({ error: 'profile_name and endpoint are required' }, 400);
    }

    const result = await createProfile(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[performance POST /profiles]', err);
    return c.json({ error: 'Failed to create performance profile' }, 500);
  }
});

// ── GET /baselines ────────────────────────────────────────────────────────────

app.get('/baselines', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await getBaselines(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[performance GET /baselines]', err);
    return c.json({ error: 'Failed to fetch performance baselines' }, 500);
  }
});

// ── GET /admin/overview ───────────────────────────────────────────────────────

app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    const expected = c.env.ADMIN_API_KEY;
    if (!expected || key !== expected) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[performance GET /admin/overview]', err);
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantPerformanceProfiling };
