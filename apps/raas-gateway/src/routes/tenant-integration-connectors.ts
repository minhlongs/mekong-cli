/**
 * Tenant Integration Connectors routes
 * Mount at: /v1/integrations
 *
 * GET  /connectors          — list connectors for authenticated tenant
 * POST /connectors          — create connector for authenticated tenant
 * GET  /logs                — fetch event logs for authenticated tenant
 * GET  /admin/overview      — admin-only platform overview (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantIntegrationConnectorsService as svc } from '../services/tenant-integration-connectors';

// Inline Bindings — avoids importing Env from index to prevent circular deps
interface Bindings {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: unknown;
}

// Narrows the discriminated union returned by service methods
type ServiceResult = { success: true; data: unknown } | { success: false; error: string };

function isOk(r: ServiceResult): r is { success: true; data: unknown } {
  return r.success;
}

const app = new Hono<{ Bindings: Bindings }>();

// ── Tenant routes (require auth) ──────────────────────────────────────────────

/**
 * GET /connectors — list all connectors belonging to the authenticated tenant
 */
app.get('/connectors', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listConnectors(c.env.DB, tenantId);
    if (!isOk(result)) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to list connectors' }, 500);
  }
});

/**
 * POST /connectors — create a new connector for the authenticated tenant
 * Body: { connector_name, connector_type, config_json?, status? }
 */
app.post('/connectors', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const { connector_name, connector_type, config_json, status } = body;

    if (!connector_name || !connector_type) {
      return c.json({ error: 'connector_name and connector_type are required' }, 400);
    }

    const result = await svc.createConnector(c.env.DB, tenantId, {
      connector_name,
      connector_type,
      config_json,
      status,
    });
    if (!isOk(result)) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create connector' }, 500);
  }
});

/**
 * GET /logs — fetch integration event logs for the authenticated tenant
 * Query param: limit (default 50)
 */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const result = await svc.getLogs(c.env.DB, tenantId, limit);
    if (!isOk(result)) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to fetch logs' }, 500);
  }
});

// ── Admin routes (X-Admin-Key) ────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide connector stats, admin only
 * Requires header: X-Admin-Key matching ADMIN_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const result = await svc.getAdminOverview(c.env.DB);
    if (!isOk(result)) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantIntegrationConnectors };
