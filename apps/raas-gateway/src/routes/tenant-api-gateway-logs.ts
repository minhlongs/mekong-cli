/**
 * Tenant API Gateway Logs routes
 * GET  /logs            — list logs for authenticated tenant
 * POST /logs            — create a log entry for authenticated tenant
 * GET  /filters         — list log filters for authenticated tenant
 * GET  /admin/overview  — platform-wide overview (X-Admin-Key protected)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiGatewayLogsService } from '../services/tenant-api-gateway-logs';

// Inline Bindings — no import from index.ts
type Bindings = {
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

const app = new Hono<{ Bindings: Bindings }>();

// ---- Tenant routes (JWT / API key auth) -------------------------------------

/**
 * GET /logs — list gateway logs for the authenticated tenant
 * Query: limit, status_code, method
 */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = c.req.query('limit') ? parseInt(c.req.query('limit')!, 10) : undefined;
    const status_code = c.req.query('status_code') ? parseInt(c.req.query('status_code')!, 10) : undefined;
    const method = c.req.query('method');

    const result = await tenantApiGatewayLogsService.listLogs(c.env.DB, tenantId, {
      limit,
      status_code,
      method: method ?? undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

/**
 * POST /logs — create a gateway log entry for the authenticated tenant
 * Body: { id, request_id?, method, path, status_code?, response_time_ms?, ip_address?, user_agent? }
 */
app.post('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.id || !body.method || !body.path) {
      return c.json({ error: 'id, method, and path are required' }, 400);
    }

    const result = await tenantApiGatewayLogsService.createLog(c.env.DB, {
      ...body,
      tenant_id: tenantId,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

/**
 * GET /filters — list log filters for the authenticated tenant
 */
app.get('/filters', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiGatewayLogsService.getFilters(c.env.DB, tenantId);

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

// ---- Admin route (X-Admin-Key protected) ------------------------------------

/**
 * GET /admin/overview — platform-wide log statistics
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantApiGatewayLogsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: any) {
    return c.json({ error: err?.message ?? 'Internal server error' }, 500);
  }
});

export { app as tenantApiGatewayLogs };
