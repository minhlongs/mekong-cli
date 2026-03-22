/**
 * Multi-Region Config routes — region-aware routing + data residency management
 *
 * Tenant (auth):
 *   GET  /config       — getRegionConfig
 *   PUT  /config       — setRegionConfig
 *   PUT  /residency    — setDataResidency
 *   GET  /optimal      — getOptimalRegion
 *
 * Public:
 *   GET  /regions      — listAvailableRegions
 *   GET  /status       — getRegionStatus
 *
 * Admin (X-Admin-Key):
 *   POST /admin/regions                  — addRegionEndpoint
 *   PUT  /admin/regions/:code/health     — updateRegionHealth
 *   POST /admin/seed                     — seedDefaultRegions
 *   GET  /admin/stats                    — getRegionStats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getRegionConfig,
  setRegionConfig,
  setDataResidency,
  getOptimalRegion,
  listAvailableRegions,
  getRegionStatus,
  addRegionEndpoint,
  updateRegionHealth,
  seedDefaultRegions,
  getRegionStats,
} from '../services/multi-region-config-service';

const app = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Tenant routes (auth required)
// ---------------------------------------------------------------------------

/** GET /config — get tenant region config */
app.get('/config', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const config = await getRegionConfig(c.env.DB, tenant.tenantId);
    if (!config) return json({ primary_region: 'auto', data_residency: 'none', routing_strategy: 'latency' });
    return json(config);
  } catch (e) {
    return json({ error: 'Failed to get region config' }, { status: 500 });
  }
});

/** PUT /config — upsert tenant region config */
app.put('/config', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const { primary_region, data_residency, routing_strategy, allowed_regions, failover_regions } = body;
  try {
    const config = await setRegionConfig(c.env.DB, tenant.tenantId, {
      primary_region, data_residency, routing_strategy, allowed_regions, failover_regions,
    });
    return json(config);
  } catch (e) {
    return json({ error: 'Failed to set region config' }, { status: 500 });
  }
});

/** PUT /residency — set data residency constraint */
app.put('/residency', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const { residency } = body;
  const valid = ['none', 'us_only', 'eu_only', 'ap_only'];
  if (!residency || !valid.includes(residency)) {
    return json({ error: `residency must be one of: ${valid.join(', ')}` }, { status: 400 });
  }
  try {
    const config = await setDataResidency(c.env.DB, tenant.tenantId, residency);
    return json(config);
  } catch (e) {
    return json({ error: 'Failed to set data residency' }, { status: 500 });
  }
});

/** GET /optimal — get optimal region for tenant */
app.get('/optimal', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const region = await getOptimalRegion(c.env.DB, tenant.tenantId);
    if (!region) return json({ error: 'No active region available' }, { status: 503 });
    return json(region);
  } catch (e) {
    return json({ error: 'Failed to determine optimal region' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Public routes
// ---------------------------------------------------------------------------

/** GET /regions — list all available region endpoints */
app.get('/regions', async (c) => {
  try {
    const regions = await listAvailableRegions(c.env.DB);
    return json({ regions });
  } catch (e) {
    return json({ error: 'Failed to list regions' }, { status: 500 });
  }
});

/** GET /status — all regions with status + latency */
app.get('/status', async (c) => {
  try {
    const regions = await getRegionStatus(c.env.DB);
    return json({ regions });
  } catch (e) {
    return json({ error: 'Failed to get region status' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin routes (X-Admin-Key required)
// ---------------------------------------------------------------------------

/** POST /admin/regions — add a region endpoint */
app.post('/admin/regions', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  const body = await c.req.json().catch(() => ({}));
  const { region_code, region_name, base_url } = body;
  if (!region_code || !region_name || !base_url) {
    return json({ error: 'region_code, region_name, base_url required' }, { status: 400 });
  }
  try {
    const endpoint = await addRegionEndpoint(c.env.DB, region_code, region_name, base_url);
    return json(endpoint, { status: 201 });
  } catch (e) {
    return json({ error: 'Failed to add region endpoint' }, { status: 500 });
  }
});

/** PUT /admin/regions/:code/health — update region health */
app.put('/admin/regions/:code/health', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  const code = c.req.param('code');
  const body = await c.req.json().catch(() => ({}));
  const { status, latency_ms } = body;
  if (!status) return json({ error: 'status required' }, { status: 400 });
  try {
    await updateRegionHealth(c.env.DB, code, status, latency_ms);
    return json({ ok: true, region_code: code, status });
  } catch (e) {
    return json({ error: 'Failed to update region health' }, { status: 500 });
  }
});

/** POST /admin/seed — seed default regions */
app.post('/admin/seed', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    await seedDefaultRegions(c.env.DB);
    return json({ ok: true, message: 'Default regions seeded (us-east, eu-west, ap-southeast)' });
  } catch (e) {
    return json({ error: 'Failed to seed regions' }, { status: 500 });
  }
});

/** GET /admin/stats — tenant count + avg latency per region */
app.get('/admin/stats', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const stats = await getRegionStats(c.env.DB);
    return json({ stats });
  } catch (e) {
    return json({ error: 'Failed to get region stats' }, { status: 500 });
  }
});

export { app as multiRegionConfig };
