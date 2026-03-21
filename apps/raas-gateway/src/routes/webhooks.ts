/**
 * Webhook admin routes — delivery logs, dead letter queue, manual retry, stats.
 * All endpoints protected by X-Admin-Key header.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { WebhookDeliveryService } from '../services/webhook-delivery-service';

export const webhooks = new Hono<{ Bindings: Env }>();

// Admin auth middleware
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

webhooks.use('/*', adminAuth());

/** GET /admin/webhooks/logs — list delivery logs with optional filters */
webhooks.get('/logs', async (c) => {
  const { tenant_id, status, limit = '50' } = c.req.query();
  const cap = Math.min(parseInt(limit, 10) || 50, 200);

  const conditions: string[] = [];
  const bindings: any[] = [];

  if (tenant_id) { conditions.push('tenant_id = ?'); bindings.push(tenant_id); }
  if (status) { conditions.push('status = ?'); bindings.push(status); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  bindings.push(cap);

  const result = await c.env.DB.prepare(
    `SELECT id, tenant_id, event_type, url, status, http_status, attempts, max_attempts,
            next_retry_at, last_attempted_at, created_at
     FROM webhook_delivery_logs ${where}
     ORDER BY created_at DESC LIMIT ?`,
  )
    .bind(...bindings)
    .all();

  return json({ logs: result.results, count: result.results.length });
});

/** GET /admin/webhooks/dead-letter — list exhausted deliveries */
webhooks.get('/dead-letter', async (c) => {
  const { limit = '50' } = c.req.query();
  const cap = Math.min(parseInt(limit, 10) || 50, 200);

  const result = await c.env.DB.prepare(
    `SELECT id, tenant_id, event_type, url, http_status, attempts, response_body,
            last_attempted_at, created_at
     FROM webhook_delivery_logs WHERE status = 'dead_letter'
     ORDER BY last_attempted_at DESC LIMIT ?`,
  )
    .bind(cap)
    .all();

  return json({ dead_letter: result.results, count: result.results.length });
});

/** POST /admin/webhooks/retry/:id — manually retry a failed delivery */
webhooks.post('/retry/:id', async (c) => {
  const deliveryId = c.req.param('id');

  // Reset status to pending so attemptDelivery can requeue
  const row = await c.env.DB.prepare(
    "SELECT id, status FROM webhook_delivery_logs WHERE id = ?",
  )
    .bind(deliveryId)
    .first<{ id: string; status: string }>();

  if (!row) return json({ error: 'Delivery not found' }, { status: 404 });

  // Allow retry from any terminal/retry state
  await c.env.DB.prepare(
    "UPDATE webhook_delivery_logs SET status='retry', next_retry_at=datetime('now'), attempts=0 WHERE id=?",
  )
    .bind(deliveryId)
    .run();

  const svc = new WebhookDeliveryService(c.env);
  const success = await svc.attemptDelivery(deliveryId);

  return json({ id: deliveryId, success, message: success ? 'Delivered' : 'Retry scheduled' });
});

/** GET /admin/webhooks/stats — delivery success rate and counts by status */
webhooks.get('/stats', async (c) => {
  const [totals, recent] = await Promise.all([
    c.env.DB.prepare(
      `SELECT status, COUNT(*) as count
       FROM webhook_delivery_logs GROUP BY status`,
    ).all(),
    c.env.DB.prepare(
      `SELECT
         COUNT(*) as total,
         SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered,
         SUM(CASE WHEN status='dead_letter' THEN 1 ELSE 0 END) as dead_letter,
         AVG(CASE WHEN http_status IS NOT NULL THEN http_status END) as avg_http_status
       FROM webhook_delivery_logs
       WHERE created_at >= datetime('now', '-24 hours')`,
    ).first<Record<string, any>>(),
  ]);

  const total = (recent?.total as number) || 0;
  const delivered = (recent?.delivered as number) || 0;
  const successRate = total > 0 ? Math.round((delivered / total) * 10000) / 100 : 0;

  return json({
    by_status: totals.results,
    last_24h: {
      total,
      delivered,
      dead_letter: recent?.dead_letter ?? 0,
      success_rate_pct: successRate,
      avg_http_status: recent?.avg_http_status ?? null,
    },
  });
});
