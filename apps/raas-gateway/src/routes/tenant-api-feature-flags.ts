/**
 * Tenant API Feature Flags routes
 * Mount at: /v1/feature-flags
 *
 * GET  /flags           — list tenant's flags (auth required)
 * POST /flags           — create flag (auth required)
 * GET  /evaluations     — list evaluations (auth required)
 * GET  /admin/overview  — platform-wide stats (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiFeatureFlagsService } from '../services/tenant-api-feature-flags';

// Inline Bindings — no import from index to avoid circular deps
interface Bindings {
  DB: D1Database;
  ADMIN_API_KEY?: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /flags — list all feature flags for the authenticated tenant
 */
app.get('/flags', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiFeatureFlagsService.listFlags(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[featureFlags GET /flags] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /flags — create a new feature flag for the authenticated tenant
 * Body: { flag_key, flag_value, description?, rollout_percentage? }
 */
app.post('/flags', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    const { flag_key, flag_value, description, rollout_percentage } = body as {
      flag_key: string;
      flag_value: number;
      description?: string;
      rollout_percentage?: number;
    };

    if (!flag_key || flag_value === undefined) {
      return c.json({ error: 'flag_key and flag_value are required' }, 400);
    }

    const result = await tenantApiFeatureFlagsService.createFlag(
      c.env.DB,
      tenantId,
      flag_key,
      flag_value,
      description,
      rollout_percentage
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[featureFlags POST /flags] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /evaluations — list flag evaluations for the authenticated tenant
 * Query params: flag_id (optional), limit (optional, default 50, max 200)
 */
app.get('/evaluations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const flagId = c.req.query('flag_id');
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;

    const result = await tenantApiFeatureFlagsService.getEvaluations(
      c.env.DB,
      tenantId,
      flagId,
      limit
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[featureFlags GET /evaluations] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide feature flag stats
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantApiFeatureFlagsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[featureFlags GET /admin/overview] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiFeatureFlags };
