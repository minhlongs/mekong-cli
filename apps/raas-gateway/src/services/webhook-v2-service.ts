/**
 * Webhook v2 Service — exponential backoff delivery + delivery reports
 * Supports HMAC-SHA256 signing, retry scheduling, and per-endpoint stats
 */

export interface WebhookConfig {
  url: string;
  secret: string;
  events: string[];
  max_retries: number;
  timeout_ms: number;
  active: boolean;
}

interface WebhookRow {
  id: string;
  tenant_id: string;
  url: string;
  secret: string;
  events: string;
  max_retries: number;
  timeout_ms: number;
  active: number;
  created_at: string;
  updated_at: string;
}

interface DeliveryRow {
  id: string;
  webhook_id: string;
  tenant_id: string;
  event_type: string;
  payload: string;
  status_code: number | null;
  response_body: string | null;
  attempt_number: number;
  next_retry_at: string | null;
  delivered: number;
  latency_ms: number | null;
  created_at: string;
}

// Exponential backoff: min(30 * 2^attempt, 3600) seconds
function calcNextRetry(attempt: number): string {
  const baseDelaySec = 30;
  const maxDelaySec = 3600;
  const delaySec = Math.min(baseDelaySec * Math.pow(2, attempt), maxDelaySec);
  const nextTime = new Date(Date.now() + delaySec * 1000);
  return nextTime.toISOString().replace('T', ' ').substring(0, 19);
}

// Sign payload with HMAC-SHA256 using Web Crypto API
async function signPayload(secret: string, payload: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(payload));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function createWebhookV2(
  db: D1Database, tenantId: string, config: Partial<WebhookConfig>
): Promise<WebhookRow> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const secret = config.secret ?? crypto.randomUUID();
  const events = JSON.stringify(config.events ?? ['*']);
  await db.prepare(
    `INSERT INTO webhook_endpoints_v2 (id, tenant_id, url, secret, events, max_retries, timeout_ms, active, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)`
  ).bind(id, tenantId, config.url ?? '', secret, events,
    config.max_retries ?? 5, config.timeout_ms ?? 10000, now, now).run();
  return db.prepare('SELECT * FROM webhook_endpoints_v2 WHERE id = ?').bind(id).first<WebhookRow>() as Promise<WebhookRow>;
}

export async function deliverWebhook(
  db: D1Database, webhookId: string, eventType: string, payload: object
): Promise<{ delivered: boolean; statusCode: number | null; deliveryId: string }> {
  const webhook = await db.prepare('SELECT * FROM webhook_endpoints_v2 WHERE id = ? AND active = 1')
    .bind(webhookId).first<WebhookRow>();
  if (!webhook) return { delivered: false, statusCode: null, deliveryId: '' };

  const payloadStr = JSON.stringify(payload);
  const signature = await signPayload(webhook.secret, payloadStr);
  const id = crypto.randomUUID();
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const start = Date.now();

  let statusCode: number | null = null;
  let responseBody: string | null = null;
  let delivered = false;

  try {
    const res = await fetch(webhook.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Webhook-Signature': signature, 'X-Event-Type': eventType },
      body: payloadStr,
      signal: AbortSignal.timeout(webhook.timeout_ms),
    });
    statusCode = res.status;
    responseBody = await res.text().then(t => t.substring(0, 500)).catch(() => null);
    delivered = res.ok;
  } catch (err) {
    responseBody = err instanceof Error ? err.message : 'fetch error';
  }

  const latencyMs = Date.now() - start;
  const nextRetryAt = !delivered ? calcNextRetry(1) : null;

  await db.prepare(
    `INSERT INTO webhook_deliveries_v2
     (id, webhook_id, tenant_id, event_type, payload, status_code, response_body, attempt_number, next_retry_at, delivered, latency_ms, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)`
  ).bind(id, webhookId, webhook.tenant_id, eventType, payloadStr,
    statusCode, responseBody, nextRetryAt, delivered ? 1 : 0, latencyMs, now).run();

  return { delivered, statusCode, deliveryId: id };
}

export async function retryDelivery(db: D1Database, deliveryId: string): Promise<{ delivered: boolean }> {
  const delivery = await db.prepare('SELECT * FROM webhook_deliveries_v2 WHERE id = ?')
    .bind(deliveryId).first<DeliveryRow>();
  if (!delivery || delivery.delivered) return { delivered: false };

  const webhook = await db.prepare('SELECT * FROM webhook_endpoints_v2 WHERE id = ? AND active = 1')
    .bind(delivery.webhook_id).first<WebhookRow>();
  if (!webhook) return { delivered: false };

  const attempt = delivery.attempt_number + 1;
  if (attempt > webhook.max_retries) return { delivered: false };

  const signature = await signPayload(webhook.secret, delivery.payload);
  const start = Date.now();
  let statusCode: number | null = null;
  let responseBody: string | null = null;
  let delivered = false;

  try {
    const res = await fetch(webhook.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Webhook-Signature': signature, 'X-Event-Type': delivery.event_type },
      body: delivery.payload,
      signal: AbortSignal.timeout(webhook.timeout_ms),
    });
    statusCode = res.status;
    responseBody = await res.text().then(t => t.substring(0, 500)).catch(() => null);
    delivered = res.ok;
  } catch (err) {
    responseBody = err instanceof Error ? err.message : 'fetch error';
  }

  const nextRetryAt = !delivered && attempt < webhook.max_retries ? calcNextRetry(attempt) : null;
  await db.prepare(
    `UPDATE webhook_deliveries_v2 SET status_code=?, response_body=?, attempt_number=?, next_retry_at=?, delivered=?, latency_ms=? WHERE id=?`
  ).bind(statusCode, responseBody, attempt, nextRetryAt, delivered ? 1 : 0, Date.now() - start, deliveryId).run();

  return { delivered };
}

export async function getDeliveryReport(db: D1Database, webhookId: string, limit = 20): Promise<DeliveryRow[]> {
  const rows = await db.prepare(
    'SELECT * FROM webhook_deliveries_v2 WHERE webhook_id = ? ORDER BY created_at DESC LIMIT ?'
  ).bind(webhookId, limit).all<DeliveryRow>();
  return rows.results ?? [];
}

export async function getPendingRetries(db: D1Database): Promise<DeliveryRow[]> {
  const rows = await db.prepare(
    `SELECT * FROM webhook_deliveries_v2 WHERE delivered = 0 AND next_retry_at IS NOT NULL AND next_retry_at <= datetime('now') LIMIT 100`
  ).all<DeliveryRow>();
  return rows.results ?? [];
}

export async function getWebhookStats(db: D1Database, tenantId: string) {
  const rows = await db.prepare(
    `SELECT webhook_id,
       COUNT(*) as total,
       SUM(delivered) as success,
       AVG(latency_ms) as avg_latency_ms
     FROM webhook_deliveries_v2 WHERE tenant_id = ?
     GROUP BY webhook_id`
  ).bind(tenantId).all<{ webhook_id: string; total: number; success: number; avg_latency_ms: number }>();
  return (rows.results ?? []).map(r => ({
    webhook_id: r.webhook_id,
    total: r.total,
    success: r.success,
    failure: r.total - r.success,
    success_rate: r.total > 0 ? Math.round((r.success / r.total) * 100) : 0,
    avg_latency_ms: Math.round(r.avg_latency_ms ?? 0),
  }));
}

export async function listWebhooksV2(db: D1Database, tenantId: string): Promise<WebhookRow[]> {
  const rows = await db.prepare('SELECT * FROM webhook_endpoints_v2 WHERE tenant_id = ? AND active = 1 ORDER BY created_at DESC')
    .bind(tenantId).all<WebhookRow>();
  return rows.results ?? [];
}

export async function updateWebhookV2(db: D1Database, webhookId: string, updates: Partial<WebhookConfig>): Promise<void> {
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const fields: string[] = ['updated_at = ?'];
  const values: unknown[] = [now];
  if (updates.url !== undefined) { fields.push('url = ?'); values.push(updates.url); }
  if (updates.secret !== undefined) { fields.push('secret = ?'); values.push(updates.secret); }
  if (updates.events !== undefined) { fields.push('events = ?'); values.push(JSON.stringify(updates.events)); }
  if (updates.max_retries !== undefined) { fields.push('max_retries = ?'); values.push(updates.max_retries); }
  if (updates.timeout_ms !== undefined) { fields.push('timeout_ms = ?'); values.push(updates.timeout_ms); }
  if (updates.active !== undefined) { fields.push('active = ?'); values.push(updates.active ? 1 : 0); }
  values.push(webhookId);
  await db.prepare(`UPDATE webhook_endpoints_v2 SET ${fields.join(', ')} WHERE id = ?`).bind(...values).run();
}

export async function deleteWebhookV2(db: D1Database, webhookId: string): Promise<void> {
  await updateWebhookV2(db, webhookId, { active: false });
}
