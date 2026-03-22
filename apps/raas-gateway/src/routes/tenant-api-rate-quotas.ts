/** Tenant API Rate Quotas — GET /quotas, POST /quotas, GET /usage, GET /admin/overview */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { listQuotas, createQuota, getUsage, getAdminOverview } from '../services/tenant-api-rate-quotas-service';

const app = new Hono<{ Bindings: Env }>();

// -- Tenant routes (auth required) --

/** GET /quotas */
app.get('/quotas', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const quotas = await listQuotas(c.env.DB, tenantId);
    return c.json({ success: true, data: quotas });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return c.json({ error }, 500);
  }
});

/** POST /quotas */
app.post('/quotas', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400);
  }

  if (!body.endpoint_pattern || typeof body.endpoint_pattern !== 'string') {
    return c.json({ error: 'endpoint_pattern required' }, 400);
  }

  try {
    const quota = await createQuota(c.env.DB, tenantId, {
      endpoint_pattern: body.endpoint_pattern,
      max_requests_per_minute: body.max_requests_per_minute as number | undefined,
      max_requests_per_hour: body.max_requests_per_hour as number | undefined,
      max_requests_per_day: body.max_requests_per_day as number | undefined,
      burst_limit: body.burst_limit as number | undefined,
    });
    return c.json({ success: true, data: quota }, 201);
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return c.json({ error }, 500);
  }
});

/** GET /usage */
app.get('/usage', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const quotaId = c.req.query('quota_id');
  try {
    const usage = await getUsage(c.env.DB, tenantId, quotaId);
    return c.json({ success: true, data: usage });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return c.json({ error }, 500);
  }
});

// -- Admin route --

/** GET /admin/overview */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return c.json({ error }, 500);
  }
});

export { app as tenantApiRateQuotas };
