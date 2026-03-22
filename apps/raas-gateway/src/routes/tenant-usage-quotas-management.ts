/**
 * Tenant Usage Quotas Management routes
 * Mount at: /v1/quotas-management
 *
 * GET  /quotas          — list tenant quotas (auth required)
 * POST /quotas          — create quota (auth required)
 * GET  /alerts          — list tenant alerts (auth required)
 * GET  /admin/overview  — platform-wide overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantUsageQuotasManagementService } from '../services/tenant-usage-quotas-management';

// Inline Bindings to avoid index.ts dependency coupling
interface Bindings {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

/** GET /quotas — list all quotas for authenticated tenant */
app.get('/quotas', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantUsageQuotasManagementService.listQuotas(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /quotas] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** POST /quotas — create a quota for authenticated tenant */
app.post('/quotas', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      resource_type: string;
      quota_limit: number;
      period?: string;
      reset_at?: string;
    }>();

    if (!body.resource_type || typeof body.quota_limit !== 'number') {
      return c.json({ error: 'resource_type and quota_limit are required' }, 400);
    }

    const result = await tenantUsageQuotasManagementService.createQuota(
      c.env.DB,
      tenantId,
      body.resource_type,
      body.quota_limit,
      body.period,
      body.reset_at
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[POST /quotas] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** GET /alerts — list quota alerts for authenticated tenant */
app.get('/alerts', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantUsageQuotasManagementService.getAlerts(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /alerts] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** GET /admin/overview — platform-wide quota overview, requires X-Admin-Key header */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantUsageQuotasManagementService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[GET /admin/overview] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantUsageQuotasManagement };
