/**
 * Tenant API Sandbox routes — isolated environments for testing APIs
 *
 * Tenant (auth):
 *   GET  /sandboxes        — listSandboxes
 *   POST /sandboxes        — createSandbox
 *   GET  /requests         — getRequests
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview   — getAdminOverview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantApiSandboxService as svc } from '../services/tenant-api-sandbox';

const app = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// GET /sandboxes — list sandbox environments for authenticated tenant
// ---------------------------------------------------------------------------

app.get('/sandboxes', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.listSandboxes(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ sandboxes: result.data, count: (result.data as unknown[]).length });
  } catch {
    return c.json({ error: 'Failed to list sandboxes' }, 500);
  }
});

// ---------------------------------------------------------------------------
// POST /sandboxes — create a sandbox environment for authenticated tenant
// ---------------------------------------------------------------------------

app.post('/sandboxes', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: { sandbox_name?: string; base_url?: string; config_json?: string };
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400);
  }
  if (!body.sandbox_name) {
    return c.json({ error: 'sandbox_name is required' }, 400);
  }
  try {
    const result = await svc.createSandbox(c.env.DB, tenantId, {
      sandbox_name: body.sandbox_name,
      base_url: body.base_url,
      config_json: body.config_json,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ sandbox: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create sandbox' }, 500);
  }
});

// ---------------------------------------------------------------------------
// GET /requests — list sandbox requests for authenticated tenant
// ---------------------------------------------------------------------------

app.get('/requests', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.getRequests(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ requests: result.data, count: (result.data as unknown[]).length });
  } catch {
    return c.json({ error: 'Failed to list requests' }, 500);
  }
});

// ---------------------------------------------------------------------------
// GET /admin/overview — admin summary (X-Admin-Key required)
// ---------------------------------------------------------------------------

app.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ overview: result.data });
  } catch {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiSandbox };
