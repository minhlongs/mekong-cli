/**
 * Mission Webhooks V3 routes
 * Per-mission callback URLs: subscriptions CRUD, delivery history, retry, stats, admin overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createSubscription,
  listSubscriptions,
  getSubscription,
  updateSubscription,
  deleteSubscription,
  getDeliveries,
  retryDelivery,
  getDeliveryStats,
  getAdminWebhookOverview,
} from '../services/mission-webhooks-v3-service';

export const missionWebhooksV3 = new Hono<{ Bindings: Env }>();

// ── Subscription endpoints (auth required) ────────────────────────────────────

/** GET /subscriptions — list all active subscriptions for tenant */
missionWebhooksV3.get('/subscriptions', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const subs = await listSubscriptions(c.env.DB, tenant.tenantId);
    return json({ subscriptions: subs, count: subs.length });
  } catch {
    return json({ error: 'Failed to list subscriptions', code: 'LIST_ERROR' }, { status: 500 });
  }
});

/** POST /subscriptions — create a new webhook subscription */
missionWebhooksV3.post('/subscriptions', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      name: string;
      url: string;
      events: string[];
      secret?: string;
      retry_policy?: string;
      max_retries?: number;
    }>();
    if (!body.name || !body.url || !Array.isArray(body.events) || body.events.length === 0) {
      return json({ error: 'name, url, and events[] are required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const sub = await createSubscription(
      c.env.DB, tenant.tenantId, body.name, body.url,
      body.events, body.secret, body.retry_policy, body.max_retries
    );
    return json({ subscription: sub }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create subscription', code: 'CREATE_ERROR' }, { status: 500 });
  }
});

/** GET /subscriptions/:subId — get subscription detail */
missionWebhooksV3.get('/subscriptions/:subId', auth(), async (c) => {
  const tenant = getTenant(c);
  const subId = c.req.param('subId');
  try {
    const sub = await getSubscription(c.env.DB, tenant.tenantId, subId);
    if (!sub) return json({ error: 'Subscription not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ subscription: sub });
  } catch {
    return json({ error: 'Failed to get subscription', code: 'GET_ERROR' }, { status: 500 });
  }
});

/** PUT /subscriptions/:subId — update subscription config */
missionWebhooksV3.put('/subscriptions/:subId', auth(), async (c) => {
  const tenant = getTenant(c);
  const subId = c.req.param('subId');
  try {
    const body = await c.req.json<{
      name?: string; url?: string; secret?: string;
      events?: string[]; retry_policy?: string; max_retries?: number; timeout_ms?: number;
    }>();
    const updated = await updateSubscription(c.env.DB, tenant.tenantId, subId, body);
    if (!updated) return json({ error: 'Subscription not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to update subscription', code: 'UPDATE_ERROR' }, { status: 500 });
  }
});

/** DELETE /subscriptions/:subId — deactivate subscription */
missionWebhooksV3.delete('/subscriptions/:subId', auth(), async (c) => {
  const tenant = getTenant(c);
  const subId = c.req.param('subId');
  try {
    const deleted = await deleteSubscription(c.env.DB, tenant.tenantId, subId);
    if (!deleted) return json({ error: 'Subscription not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to delete subscription', code: 'DELETE_ERROR' }, { status: 500 });
  }
});

// ── Delivery endpoints (auth required) ───────────────────────────────────────

/** GET /deliveries — delivery history for tenant, optional ?subscription_id=&limit= */
missionWebhooksV3.get('/deliveries', auth(), async (c) => {
  const tenant = getTenant(c);
  const subId = c.req.query('subscription_id');
  const limit = parseInt(c.req.query('limit') ?? '50', 10);
  try {
    const deliveries = await getDeliveries(c.env.DB, tenant.tenantId, subId, limit);
    return json({ deliveries, count: deliveries.length });
  } catch {
    return json({ error: 'Failed to get deliveries', code: 'DELIVERY_ERROR' }, { status: 500 });
  }
});

/** POST /deliveries/:deliveryId/retry — reset delivery for retry */
missionWebhooksV3.post('/deliveries/:deliveryId/retry', auth(), async (c) => {
  const tenant = getTenant(c);
  const deliveryId = c.req.param('deliveryId');
  try {
    const result = await retryDelivery(c.env.DB, tenant.tenantId, deliveryId);
    if (!result.queued) {
      return json({ error: 'Delivery not eligible for retry', code: 'RETRY_INELIGIBLE' }, { status: 400 });
    }
    return json({ success: true, queued: true });
  } catch {
    return json({ error: 'Failed to queue retry', code: 'RETRY_ERROR' }, { status: 500 });
  }
});

// ── Stats endpoint (auth required) ───────────────────────────────────────────

/** GET /stats — delivery stats for tenant */
missionWebhooksV3.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await getDeliveryStats(c.env.DB, tenant.tenantId);
    return json({ stats });
  } catch {
    return json({ error: 'Failed to get stats', code: 'STATS_ERROR' }, { status: 500 });
  }
});

// ── Admin endpoint (X-Admin-Key required) ────────────────────────────────────

/** GET /admin/overview — platform-wide webhook stats */
missionWebhooksV3.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin key required', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  try {
    const overview = await getAdminWebhookOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to get admin overview', code: 'ADMIN_ERROR' }, { status: 500 });
  }
});
