/**
 * API Gateway Middleware Config routes — per-tenant middleware chain management
 * Mount path: /api-gateway-middleware
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import * as svc from '../services/api-gateway-middleware-service';

const app = new Hono<{ Bindings: Env }>();

// GET /configs — list tenant middleware configs
app.get('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listConfigs(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /configs — create a new middleware config
app.post('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name: string;
      middleware_type: string;
      description?: string;
      config_json?: Record<string, unknown>;
      priority?: number;
      is_active?: boolean;
      endpoint_pattern?: string;
    }>();
    if (!body.name) return c.json({ error: 'name is required' }, 400);
    if (!body.middleware_type) return c.json({ error: 'middleware_type is required' }, 400);
    const data = await svc.createConfig(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /configs/:id — update a middleware config
app.put('/configs/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name?: string;
      description?: string;
      middleware_type?: string;
      config_json?: Record<string, unknown>;
      priority?: number;
      is_active?: boolean;
      endpoint_pattern?: string;
    }>();
    const data = await svc.updateConfig(c.env.DB, tenantId, c.req.param('id'), body);
    if (!data) return c.json({ error: 'Config not found' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// DELETE /configs/:id — delete a middleware config
app.delete('/configs/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await svc.deleteConfig(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return c.json({ error: 'Config not found' }, 404);
    return c.json({ success: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /reorder — reorder middleware priorities
app.post('/reorder', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ ordered_ids: string[] }>();
    if (!Array.isArray(body.ordered_ids) || body.ordered_ids.length === 0) {
      return c.json({ error: 'ordered_ids array is required' }, 400);
    }
    await svc.reorderConfigs(c.env.DB, tenantId, body.ordered_ids);
    return c.json({ success: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /templates — list public middleware templates (no auth)
app.get('/templates', async (c) => {
  try {
    const data = await svc.listTemplates(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /logs — execution logs for tenant
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '100', 10);
    const data = await svc.getExecutionLogs(c.env.DB, tenantId, limit);
    return c.json({ success: true, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /preview — preview middleware chain for an endpoint pattern
app.get('/preview', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const endpoint = c.req.query('endpoint') ?? '*';
    const data = await svc.getChainPreview(c.env.DB, tenantId, endpoint);
    return c.json({ success: true, endpoint, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — admin stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as apiGatewayMiddleware };
