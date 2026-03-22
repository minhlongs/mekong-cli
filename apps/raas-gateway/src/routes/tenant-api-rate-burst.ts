/**
 * Tenant API Rate Burst routes — token-bucket config and event management
 *
 * Tenant (auth): GET /configs, POST /configs, GET /events
 * Admin (X-Admin-Key): GET /admin/overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantApiRateBurstService } from '../services/tenant-api-rate-burst-service';

const app = new Hono<{ Bindings: Env }>();

const isAdmin = (c: { req: { header: (k: string) => string | undefined }; env: Env }) =>
  Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);

const dbErr = (err: unknown) => ({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' });

app.get('/configs', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    return c.json({ success: true, data: await tenantApiRateBurstService.listConfigs(c.env.DB, tenant.tenantId) });
  } catch (err) { return json(dbErr(err), { status: 500 }); }
});

app.post('/configs', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.endpoint_pattern) {
    return json({ error: 'endpoint_pattern required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const result = await tenantApiRateBurstService.createConfig(c.env.DB, tenant.tenantId, {
      endpoint_pattern: body.endpoint_pattern as string,
      bucket_size: body.bucket_size as number | undefined,
      refill_rate: body.refill_rate as number | undefined,
      refill_interval_ms: body.refill_interval_ms as number | undefined,
    });
    return c.json({ success: true, data: result }, 201);
  } catch (err) { return json(dbErr(err), { status: 500 }); }
});

app.get('/events', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = parseInt(c.req.query('limit') ?? '100', 10);
  try {
    return c.json({ success: true, data: await tenantApiRateBurstService.getEvents(c.env.DB, tenant.tenantId, limit) });
  } catch (err) { return json(dbErr(err), { status: 500 }); }
});

app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    return c.json({ success: true, data: await tenantApiRateBurstService.getAdminOverview(c.env.DB) });
  } catch (err) { return json(dbErr(err), { status: 500 }); }
});

export { app as tenantApiRateBurst };
