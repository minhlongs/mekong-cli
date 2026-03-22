/**
 * Tenant Integration Marketplace routes
 * Mount at: /v1/tenant-integrations
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  listIntegrations,
  createIntegration,
  getLogs,
  getAdminOverview,
} from '../services/tenant-integration-marketplace';

const app = new Hono<{ Bindings: Env }>();

/** GET /integrations — list tenant integrations */
app.get('/integrations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await listIntegrations(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** POST /integrations — create a new integration for the tenant */
app.post('/integrations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      integration_type: string;
      provider_name: string;
      config_json?: string;
      status?: string;
    }>();

    if (!body.integration_type || !body.provider_name) {
      return c.json({ success: false, error: 'integration_type and provider_name are required' }, 400);
    }

    const integration = await createIntegration(c.env.DB, tenantId, body);
    return c.json({ success: true, data: integration }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /logs — list integration logs for the tenant */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await getLogs(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /admin/overview — admin: platform-wide integration overview */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const data = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as tenantIntegrationMarketplace };
