/**
 * Tenant API Load Balancing routes
 *
 * Tenant (auth required):
 *   GET  /configs              — list tenant load balancer configs
 *   POST /configs              — create a new load balancer config
 *   GET  /targets              — list targets for a config (?config_id=)
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview       — aggregate stats across all tenants
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { listConfigs, createConfig, getTargets, getAdminOverview } from '../services/tenant-api-load-balancing';

const app = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Admin guard
// ---------------------------------------------------------------------------

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Tenant routes
// ---------------------------------------------------------------------------

/** GET /configs — list all load balancer configs for authenticated tenant */
app.get('/configs', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await listConfigs(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list configs' }, 500);
  }
});

/** POST /configs — create a new load balancer config for authenticated tenant */
app.post('/configs', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400);
  }

  if (!body.config_name || typeof body.config_name !== 'string') {
    return c.json({ error: 'config_name is required' }, 400);
  }

  try {
    const result = await createConfig(c.env.DB, tenant.tenantId, {
      config_name: body.config_name,
      algorithm: body.algorithm as string | undefined,
      health_check_interval_ms: body.health_check_interval_ms as number | undefined,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create config' }, 500);
  }
});

/** GET /targets — list targets for a config owned by authenticated tenant */
app.get('/targets', auth(), async (c) => {
  const tenant = getTenant(c);
  const configId = c.req.query('config_id');

  if (!configId) {
    return c.json({ error: 'config_id query param is required' }, 400);
  }

  try {
    const result = await getTargets(c.env.DB, tenant.tenantId, configId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list targets' }, 500);
  }
});

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

/** GET /admin/overview — aggregate load balancer stats across all tenants */
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const result = await getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to load admin overview' }, 500);
  }
});

export { app as tenantApiLoadBalancing };
