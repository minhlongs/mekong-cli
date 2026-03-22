/**
 * Tenant Webhooks V3 routes — subscription CRUD, delivery management, event types, stats.
 * Auth: JWT/API key via auth middleware. Admin routes require X-Admin-Key header.
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantWebhooksV3Service as svc } from '../services/tenant-webhooks-v3-service';
import { json } from '../utils/response';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// --- Subscription endpoints (auth required) ---

app.get('/subscriptions', auth(), async (c) => {
  const tenant = getTenant(c);
  const data = await svc.listSubscriptions(c.env.DB, tenant.tenantId);
  return json({ subscriptions: data });
});

app.post('/subscriptions', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (!body.url) return json({ error: 'url is required' }, { status: 400 });
  const result = await svc.createSubscription(c.env.DB, tenant.tenantId, body);
  return json(result, { status: 201 });
});

app.get('/subscriptions/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const sub = await svc.getSubscription(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!sub) return json({ error: 'Subscription not found' }, { status: 404 });
  return json(sub);
});

app.put('/subscriptions/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const updated = await svc.updateSubscription(c.env.DB, tenant.tenantId, c.req.param('id'), body);
  if (!updated) return json({ error: 'Subscription not found or no valid fields' }, { status: 404 });
  return json(updated);
});

app.delete('/subscriptions/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  await svc.deleteSubscription(c.env.DB, tenant.tenantId, c.req.param('id'));
  return json({ deleted: true });
});

app.post('/subscriptions/:id/test', auth(), async (c) => {
  const tenant = getTenant(c);
  const result = await svc.testSubscription(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!result) return json({ error: 'Subscription not found' }, { status: 404 });
  return json(result);
});

app.get('/subscriptions/:id/deliveries', auth(), async (c) => {
  const tenant = getTenant(c);
  const status = c.req.query('status');
  const data = await svc.listDeliveries(c.env.DB, tenant.tenantId, c.req.param('id'), status ? { status } : undefined);
  return json({ deliveries: data });
});

// --- Delivery retry (auth required) ---

app.post('/deliveries/:id/retry', auth(), async (c) => {
  await svc.retryDelivery(c.env.DB, c.req.param('id'));
  return json({ queued: true });
});

// --- Event types (public) ---

app.get('/event-types', async (c) => {
  const data = await svc.listEventTypes(c.env.DB);
  return json({ event_types: data });
});

// --- Stats (auth required) ---

app.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  const data = await svc.getDeliveryStats(c.env.DB, tenant.tenantId);
  return json({ stats: data });
});

// --- Admin overview (admin key required) ---

app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  const data = await svc.getAdminOverview(c.env.DB);
  return json(data);
});

export { app as tenantWebhooksV3 };
