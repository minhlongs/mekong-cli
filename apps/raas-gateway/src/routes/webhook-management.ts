/**
 * Webhook management routes — tenant-facing: event types, test delivery, config.
 * Distinct from admin webhooks (routes/webhooks.ts).
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const webhookManagement = new Hono<{ Bindings: Env }>();
webhookManagement.use('*', auth());

const EVENT_TYPES = [
  { type: 'mission.completed',        description: 'A mission finished successfully' },
  { type: 'mission.failed',           description: 'A mission failed after all retries' },
  { type: 'credits.low',              description: 'Credit balance dropped below threshold' },
  { type: 'credits.exhausted',        description: 'Credit balance reached zero' },
  { type: 'subscription.created',     description: 'A new subscription was created' },
  { type: 'subscription.cancelled',   description: 'A subscription was cancelled' },
  { type: 'subscription.renewed',     description: 'A subscription was renewed' },
  { type: 'team.member_invited',      description: 'A team member was invited' },
];

/** GET /v1/webhooks/events — list available webhook event types */
webhookManagement.get('/events', (c) => {
  return json({ events: EVENT_TYPES });
});

/** POST /v1/webhooks/test — send a test webhook to tenant's configured URL */
webhookManagement.post('/test', async (c) => {
  const tenant = getTenant(c);

  const row = await c.env.DB.prepare(
    'SELECT webhook_url FROM tenants WHERE id = ?'
  )
    .bind(tenant.tenantId)
    .first<{ webhook_url: string | null }>();

  if (!row?.webhook_url) {
    return json({ error: 'No webhook_url configured', code: 'NO_WEBHOOK_URL' }, { status: 400 });
  }

  const payload = {
    event: 'test',
    data: {
      message: 'Webhook test from Mekong RaaS',
      timestamp: new Date().toISOString(),
    },
    tenant_id: tenant.tenantId,
  };

  const start = Date.now();
  try {
    const res = await fetch(row.webhook_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return json({
      success: res.ok,
      status_code: res.status,
      response_time_ms: Date.now() - start,
    });
  } catch (err) {
    return json({
      success: false,
      status_code: 0,
      response_time_ms: Date.now() - start,
      error: err instanceof Error ? err.message : 'Delivery failed',
    });
  }
});

/** GET /v1/webhooks/config — tenant's current webhook configuration */
webhookManagement.get('/config', async (c) => {
  const tenant = getTenant(c);

  const row = await c.env.DB.prepare(
    'SELECT webhook_url, notify_email, notify_telegram FROM tenants WHERE id = ?'
  )
    .bind(tenant.tenantId)
    .first<{ webhook_url: string | null; notify_email: string | null; notify_telegram: string | null }>();

  return json({
    webhook_url:      row?.webhook_url      ?? null,
    notify_email:     row?.notify_email     ?? null,
    notify_telegram:  row?.notify_telegram  ?? null,
    events_subscribed: 'all',
  });
});
