/**
 * Tenant API Gateway Logs routes — list, record, and summarize gateway logs per tenant
 * Mounted at /v1/gateway-logs in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiGatewayLogsService } from '../services/tenant-api-gateway-logs-service';

const app = new Hono<{ Bindings: Env }>();

// GET /logs — list gateway logs for authenticated tenant
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : 50;
    const offset = c.req.query('offset') ? Number(c.req.query('offset')) : 0;
    const method = c.req.query('method');
    const statusCode = c.req.query('status_code') ? Number(c.req.query('status_code')) : undefined;

    const logs = await tenantApiGatewayLogsService.listLogs(c.env.DB, tenantId, {
      limit,
      offset,
      method,
      status_code: statusCode,
    });

    return c.json({ success: true, data: logs, total: logs.length });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /logs — record a gateway log entry for authenticated tenant
app.post('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      method?: string;
      path?: string;
      status_code?: number;
      response_time_ms?: number;
      request_size?: number;
      response_size?: number;
      ip_address?: string;
      user_agent?: string;
    }>();

    if (!body.method || !body.path || body.status_code === undefined) {
      return c.json({ error: 'method, path, and status_code are required' }, 400);
    }

    const log = await tenantApiGatewayLogsService.recordLog(c.env.DB, tenantId, {
      method: body.method,
      path: body.path,
      status_code: body.status_code,
      response_time_ms: body.response_time_ms,
      request_size: body.request_size,
      response_size: body.response_size,
      ip_address: body.ip_address,
      user_agent: body.user_agent,
    });

    return c.json({ success: true, data: log }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /summaries — get log summaries for authenticated tenant
app.get('/summaries', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : 10;

    const summaries = await tenantApiGatewayLogsService.getSummaries(c.env.DB, tenantId, limit);
    return c.json({ success: true, data: summaries, total: summaries.length });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /admin/overview — admin-only cross-tenant stats
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const overview = await tenantApiGatewayLogsService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as tenantApiGatewayLogs };
