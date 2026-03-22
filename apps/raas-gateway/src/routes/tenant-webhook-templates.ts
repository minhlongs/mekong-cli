/**
 * Tenant Webhook Templates routes
 * Mount at: /v1/tenant-webhook-templates
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantWebhookTemplatesService } from '../services/tenant-webhook-templates-service';

const { listTemplates, createTemplate, getUsage, getAdminOverview } =
  tenantWebhookTemplatesService;

const app = new Hono<{ Bindings: Env }>();

/** GET /templates — list webhook templates for the tenant */
app.get('/templates', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await listTemplates(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** POST /templates — create a new webhook template for the tenant */
app.post('/templates', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      template_name: string;
      event_type: string;
      url_pattern: string;
      headers_json?: string;
      payload_template?: string;
      is_active?: number;
    }>();

    if (!body.template_name || !body.event_type || !body.url_pattern) {
      return c.json({ success: false, error: 'template_name, event_type, and url_pattern are required' }, 400);
    }

    const data = await createTemplate(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /usage — list template usage logs for the tenant */
app.get('/usage', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await getUsage(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /admin/overview — admin: platform-wide webhook templates overview */
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

export { app as tenantWebhookTemplates };
