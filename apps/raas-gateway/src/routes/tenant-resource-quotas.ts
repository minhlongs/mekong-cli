/**
 * Tenant Resource Quotas routes
 * Mount at: /v1/quotas
 *
 * Public:  GET /definitions
 * Admin:   POST /definitions, PUT /definitions/:resourceType, PUT /quotas/:resourceType, POST /reset/:resourceType, GET /admin/overview
 * Auth:    GET /quotas, GET /check/:resourceType, POST /usage/:resourceType, GET /alerts, POST /alerts/:id/acknowledge
 */

import { Hono, type Context } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantResourceQuotasService as svc } from '../services/tenant-resource-quotas-service';

type AppEnv = {
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
};

const app = new Hono<AppEnv>();

/** Validate admin API key from request header */
function isAdmin(c: Context<AppEnv>): boolean {
  const key = c.req.header('X-Admin-API-Key') ?? c.req.header('X-Api-Key');
  return !!key && key === c.env.ADMIN_API_KEY;
}

// ── Public ────────────────────────────────────────────────────────────────────

/** GET /definitions — list all quota type definitions */
app.get('/definitions', async (c) => {
  try {
    const data = await svc.listDefinitions(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas GET /definitions]', err);
    return c.json({ success: false, error: 'Failed to list definitions' }, 500);
  }
});

// ── Admin ─────────────────────────────────────────────────────────────────────

/** POST /definitions — create a new quota definition */
app.post('/definitions', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    if (!body.resource_type || !body.display_name || body.default_limit === undefined) {
      return c.json({ success: false, error: 'resource_type, display_name, default_limit required' }, 400);
    }
    const data = await svc.createDefinition(c.env.DB, {
      resource_type: String(body.resource_type),
      display_name: String(body.display_name),
      description: body.description ? String(body.description) : null,
      default_limit: Number(body.default_limit),
      unit: body.unit ? String(body.unit) : 'count',
      enforcement: body.enforcement ? String(body.enforcement) : 'soft',
    });
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[quotas POST /definitions]', err);
    return c.json({ success: false, error: 'Failed to create definition' }, 500);
  }
});

/** PUT /definitions/:resourceType — update a quota definition */
app.put('/definitions/:resourceType', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const resourceType = c.req.param('resourceType');
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    const data = await svc.updateDefinition(c.env.DB, resourceType, {
      display_name: body.display_name ? String(body.display_name) : undefined,
      description: body.description !== undefined ? String(body.description) : undefined,
      default_limit: body.default_limit !== undefined ? Number(body.default_limit) : undefined,
      unit: body.unit ? String(body.unit) : undefined,
      enforcement: body.enforcement ? String(body.enforcement) : undefined,
    });
    if (!data) return c.json({ success: false, error: 'Definition not found or no fields to update' }, 404);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas PUT /definitions/:resourceType]', err);
    return c.json({ success: false, error: 'Failed to update definition' }, 500);
  }
});

/** PUT /quotas/:resourceType — set tenant quota limit (admin, body: { tenant_id, limit }) */
app.put('/quotas/:resourceType', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const resourceType = c.req.param('resourceType');
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    if (!body.tenant_id || body.limit === undefined) {
      return c.json({ success: false, error: 'tenant_id and limit required' }, 400);
    }
    const data = await svc.setTenantQuota(c.env.DB, String(body.tenant_id), resourceType, Number(body.limit));
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas PUT /quotas/:resourceType]', err);
    return c.json({ success: false, error: 'Failed to set quota' }, 500);
  }
});

/** POST /reset/:resourceType — reset usage for a tenant (admin, body: { tenant_id }) */
app.post('/reset/:resourceType', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const resourceType = c.req.param('resourceType');
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    if (!body.tenant_id) return c.json({ success: false, error: 'tenant_id required' }, 400);
    await svc.resetUsage(c.env.DB, String(body.tenant_id), resourceType);
    return c.json({ success: true, reset: true });
  } catch (err) {
    console.error('[quotas POST /reset/:resourceType]', err);
    return c.json({ success: false, error: 'Failed to reset usage' }, 500);
  }
});

/** GET /admin/overview — global usage stats and top consumers */
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get overview' }, 500);
  }
});

// ── Auth ──────────────────────────────────────────────────────────────────────

app.use('/quotas', auth());
app.use('/check/*', auth());
app.use('/usage/*', auth());
app.use('/alerts', auth());
app.use('/alerts/*', auth());

/** GET /quotas — list all quotas for the authenticated tenant */
app.get('/quotas', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getTenantQuotas(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas GET /quotas]', err);
    return c.json({ success: false, error: 'Failed to get quotas' }, 500);
  }
});

/** GET /check/:resourceType — check if tenant is within quota */
app.get('/check/:resourceType', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const resourceType = c.req.param('resourceType');
    const data = await svc.checkQuota(c.env.DB, tenantId, resourceType);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas GET /check/:resourceType]', err);
    return c.json({ success: false, error: 'Failed to check quota' }, 500);
  }
});

/** POST /usage/:resourceType — increment usage (body: { amount? }) */
app.post('/usage/:resourceType', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const resourceType = c.req.param('resourceType');
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    const amount = body.amount !== undefined ? Number(body.amount) : 1;
    await svc.incrementUsage(c.env.DB, tenantId, resourceType, amount);
    const data = await svc.checkQuota(c.env.DB, tenantId, resourceType);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas POST /usage/:resourceType]', err);
    return c.json({ success: false, error: 'Failed to increment usage' }, 500);
  }
});

/** GET /alerts — list quota alerts for the authenticated tenant */
app.get('/alerts', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listAlerts(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[quotas GET /alerts]', err);
    return c.json({ success: false, error: 'Failed to list alerts' }, 500);
  }
});

/** POST /alerts/:id/acknowledge — acknowledge a quota alert */
app.post('/alerts/:id/acknowledge', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const alertId = c.req.param('id');
    const acknowledged = await svc.acknowledgeAlert(c.env.DB, tenantId, alertId);
    if (!acknowledged) return c.json({ success: false, error: 'Alert not found' }, 404);
    return c.json({ success: true, acknowledged: true });
  } catch (err) {
    console.error('[quotas POST /alerts/:id/acknowledge]', err);
    return c.json({ success: false, error: 'Failed to acknowledge alert' }, 500);
  }
});

export { app as tenantResourceQuotas };
