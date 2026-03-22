/**
 * Admin Tenant Communication routes — send messages to tenants, manage templates
 * All endpoints require X-Admin-Key header. Mount path: /admin/tenant-communication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminTenantCommunicationService as svc } from '../services/admin-tenant-communication-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard for all routes
app.use('*', async (c, next) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /messages — list messages (?tenant_id= &message_type= &limit=)
app.get('/messages', async (c) => {
  try {
    const tenantId = c.req.query('tenant_id');
    const messageType = c.req.query('message_type');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const messages = await svc.listMessages(c.env.DB, tenantId, messageType, limit);
    return c.json({ messages, count: messages.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /messages — send a message to a tenant
app.post('/messages', async (c) => {
  try {
    const body = await c.req.json<{
      tenant_id: string;
      subject: string;
      body: string;
      message_type?: string;
      priority?: string;
      sent_by?: string;
    }>();
    if (!body.tenant_id) return c.json({ error: 'tenant_id is required' }, 400);
    if (!body.subject) return c.json({ error: 'subject is required' }, 400);
    if (!body.body) return c.json({ error: 'body is required' }, 400);
    const message = await svc.createMessage(c.env.DB, body.tenant_id, body.subject, body.body, {
      messageType: body.message_type,
      priority: body.priority,
      sentBy: body.sent_by,
    });
    return c.json(message, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /templates — list message templates (?category=)
app.get('/templates', async (c) => {
  try {
    const category = c.req.query('category');
    const templates = await svc.getTemplates(c.env.DB, category);
    return c.json({ templates, count: templates.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — message stats summary
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminTenantCommunication };
