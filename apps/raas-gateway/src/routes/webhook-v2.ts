/**
 * Webhook v2 routes — exponential backoff delivery + delivery reports
 * Endpoints: CRUD for webhook endpoints, delivery history, test event, stats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createWebhookV2,
  deliverWebhook,
  deleteWebhookV2,
  getDeliveryReport,
  getWebhookStats,
  listWebhooksV2,
  updateWebhookV2,
} from '../services/webhook-v2-service';

export const webhookV2 = new Hono<{ Bindings: Env }>();
webhookV2.use('*', auth());

/** POST /webhooks-v2 — create webhook endpoint */
webhookV2.post('/', async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      url: string;
      secret?: string;
      events?: string[];
      max_retries?: number;
      timeout_ms?: number;
    }>();
    if (!body.url) {
      return json({ error: 'url is required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const webhook = await createWebhookV2(c.env.DB, tenant.tenantId, body);
    return json({ webhook }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to create webhook', code: 'CREATE_ERROR' }, { status: 500 });
  }
});

/** GET /webhooks-v2 — list webhook endpoints */
webhookV2.get('/', async (c) => {
  const tenant = getTenant(c);
  try {
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    return json({ webhooks, count: webhooks.length });
  } catch {
    return json({ error: 'Failed to list webhooks', code: 'LIST_ERROR' }, { status: 500 });
  }
});

/** GET /webhooks-v2/stats — delivery stats per endpoint */
webhookV2.get('/stats', async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await getWebhookStats(c.env.DB, tenant.tenantId);
    return json({ stats });
  } catch {
    return json({ error: 'Failed to get stats', code: 'STATS_ERROR' }, { status: 500 });
  }
});

/** GET /webhooks-v2/:id — get webhook details */
webhookV2.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    const webhook = webhooks.find(w => w.id === id);
    if (!webhook) return json({ error: 'Webhook not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ webhook });
  } catch {
    return json({ error: 'Failed to get webhook', code: 'GET_ERROR' }, { status: 500 });
  }
});

/** PUT /webhooks-v2/:id — update webhook config */
webhookV2.put('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const body = await c.req.json<{
      url?: string;
      secret?: string;
      events?: string[];
      max_retries?: number;
      timeout_ms?: number;
      active?: boolean;
    }>();
    // Verify ownership
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    const existing = webhooks.find(w => w.id === id);
    if (!existing) return json({ error: 'Webhook not found', code: 'NOT_FOUND' }, { status: 404 });
    await updateWebhookV2(c.env.DB, id, body);
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to update webhook', code: 'UPDATE_ERROR' }, { status: 500 });
  }
});

/** DELETE /webhooks-v2/:id — soft delete webhook */
webhookV2.delete('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    const existing = webhooks.find(w => w.id === id);
    if (!existing) return json({ error: 'Webhook not found', code: 'NOT_FOUND' }, { status: 404 });
    await deleteWebhookV2(c.env.DB, id);
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to delete webhook', code: 'DELETE_ERROR' }, { status: 500 });
  }
});

/** GET /webhooks-v2/:id/deliveries — delivery report */
webhookV2.get('/:id/deliveries', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  const limit = parseInt(c.req.query('limit') ?? '20', 10);
  try {
    // Verify ownership
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    if (!webhooks.find(w => w.id === id)) {
      return json({ error: 'Webhook not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    const deliveries = await getDeliveryReport(c.env.DB, id, Math.min(limit, 100));
    return json({ deliveries, count: deliveries.length });
  } catch {
    return json({ error: 'Failed to get deliveries', code: 'REPORT_ERROR' }, { status: 500 });
  }
});

/** POST /webhooks-v2/:id/test — send test event */
webhookV2.post('/:id/test', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const webhooks = await listWebhooksV2(c.env.DB, tenant.tenantId);
    if (!webhooks.find(w => w.id === id)) {
      return json({ error: 'Webhook not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    const result = await deliverWebhook(c.env.DB, id, 'test.ping', {
      event: 'test.ping',
      message: 'Webhook v2 test delivery from RaaS Gateway',
      timestamp: new Date().toISOString(),
      tenant_id: tenant.tenantId,
    });
    return json(result);
  } catch {
    return json({ error: 'Failed to send test event', code: 'TEST_ERROR' }, { status: 500 });
  }
});
