/**
 * Mission Webhooks V3 Service
 * Per-mission callback URLs with configurable retry, delivery guarantees, and HMAC signing
 */

interface SubscriptionRow {
  id: string;
  tenant_id: string;
  name: string;
  url: string;
  secret: string | null;
  events: string;
  retry_policy: string;
  max_retries: number;
  timeout_ms: number;
  is_active: number;
  created_at: string;
  updated_at: string | null;
}

interface DeliveryRow {
  id: string;
  subscription_id: string;
  tenant_id: string;
  event_type: string;
  payload: string;
  status: string;
  attempt_count: number;
  last_attempt_at: string | null;
  next_retry_at: string | null;
  response_status: number | null;
  response_body: string | null;
  duration_ms: number | null;
  created_at: string;
}

function now(): string {
  return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

// Calculate next retry time based on policy
function calcNextRetry(policy: string, attempt: number): string {
  const base = policy === 'linear' ? 60 : 30; // seconds
  const delay = policy === 'none' ? 0
    : policy === 'linear' ? base * attempt
    : Math.min(base * Math.pow(2, attempt - 1), 3600); // exponential cap 1h
  return new Date(Date.now() + delay * 1000).toISOString().replace('T', ' ').substring(0, 19);
}

// HMAC-SHA256 signature for payload verification
async function signPayload(secret: string, payload: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(payload));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function createSubscription(
  db: D1Database, tenantId: string, name: string, url: string,
  events: string[], secret?: string, retryPolicy = 'exponential', maxRetries = 5
): Promise<SubscriptionRow> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO webhook_subscriptions_v3
     (id, tenant_id, name, url, secret, events, retry_policy, max_retries, is_active, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)`
  ).bind(id, tenantId, name, url, secret ?? null, JSON.stringify(events), retryPolicy, maxRetries, now()).run();
  return db.prepare('SELECT * FROM webhook_subscriptions_v3 WHERE id = ?').bind(id).first<SubscriptionRow>() as Promise<SubscriptionRow>;
}

export async function listSubscriptions(db: D1Database, tenantId: string): Promise<SubscriptionRow[]> {
  const rows = await db.prepare(
    'SELECT * FROM webhook_subscriptions_v3 WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC'
  ).bind(tenantId).all<SubscriptionRow>();
  return rows.results ?? [];
}

export async function getSubscription(db: D1Database, tenantId: string, subId: string): Promise<SubscriptionRow | null> {
  return db.prepare(
    'SELECT * FROM webhook_subscriptions_v3 WHERE id = ? AND tenant_id = ? AND is_active = 1'
  ).bind(subId, tenantId).first<SubscriptionRow>();
}

export async function updateSubscription(
  db: D1Database, tenantId: string, subId: string,
  updates: Partial<{ name: string; url: string; secret: string; events: string[]; retry_policy: string; max_retries: number; timeout_ms: number }>
): Promise<boolean> {
  const sub = await getSubscription(db, tenantId, subId);
  if (!sub) return false;
  const fields: string[] = ['updated_at = ?'];
  const values: unknown[] = [now()];
  if (updates.name !== undefined) { fields.push('name = ?'); values.push(updates.name); }
  if (updates.url !== undefined) { fields.push('url = ?'); values.push(updates.url); }
  if (updates.secret !== undefined) { fields.push('secret = ?'); values.push(updates.secret); }
  if (updates.events !== undefined) { fields.push('events = ?'); values.push(JSON.stringify(updates.events)); }
  if (updates.retry_policy !== undefined) { fields.push('retry_policy = ?'); values.push(updates.retry_policy); }
  if (updates.max_retries !== undefined) { fields.push('max_retries = ?'); values.push(updates.max_retries); }
  if (updates.timeout_ms !== undefined) { fields.push('timeout_ms = ?'); values.push(updates.timeout_ms); }
  values.push(subId);
  await db.prepare(`UPDATE webhook_subscriptions_v3 SET ${fields.join(', ')} WHERE id = ?`).bind(...values).run();
  return true;
}

export async function deleteSubscription(db: D1Database, tenantId: string, subId: string): Promise<boolean> {
  const sub = await getSubscription(db, tenantId, subId);
  if (!sub) return false;
  await db.prepare('UPDATE webhook_subscriptions_v3 SET is_active = 0, updated_at = ? WHERE id = ?')
    .bind(now(), subId).run();
  return true;
}

export async function triggerWebhook(
  db: D1Database, tenantId: string, eventType: string, payload: object
): Promise<{ triggered: number; deliveryIds: string[] }> {
  // Find active subscriptions matching event type for this tenant
  const subs = await db.prepare(
    'SELECT * FROM webhook_subscriptions_v3 WHERE tenant_id = ? AND is_active = 1'
  ).bind(tenantId).all<SubscriptionRow>();

  const matching = (subs.results ?? []).filter(s => {
    const evts: string[] = JSON.parse(s.events);
    return evts.includes('*') || evts.includes(eventType);
  });

  const deliveryIds: string[] = [];
  const payloadStr = JSON.stringify({ event: eventType, data: payload, timestamp: new Date().toISOString() });

  for (const sub of matching) {
    const deliveryId = crypto.randomUUID();
    const t = now();
    // Create pending delivery record
    await db.prepare(
      `INSERT INTO webhook_deliveries_v3
       (id, subscription_id, tenant_id, event_type, payload, status, attempt_count, created_at)
       VALUES (?, ?, ?, ?, ?, 'pending', 0, ?)`
    ).bind(deliveryId, sub.id, tenantId, eventType, payloadStr, t).run();

    // Attempt delivery immediately
    const start = Date.now();
    let responseStatus: number | null = null;
    let responseBody: string | null = null;
    let delivered = false;

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Event-Type': eventType,
        'X-Delivery-Id': deliveryId,
      };
      if (sub.secret) {
        headers['X-Webhook-Signature'] = await signPayload(sub.secret, payloadStr);
      }
      const res = await fetch(sub.url, {
        method: 'POST',
        headers,
        body: payloadStr,
        signal: AbortSignal.timeout(sub.timeout_ms),
      });
      responseStatus = res.status;
      responseBody = await res.text().then(tx => tx.substring(0, 500)).catch(() => null);
      delivered = res.ok;
    } catch (err) {
      responseBody = err instanceof Error ? err.message : 'fetch error';
    }

    const duration = Date.now() - start;
    const status = delivered ? 'delivered' : (sub.retry_policy === 'none' ? 'failed' : 'retrying');
    const nextRetry = !delivered && sub.retry_policy !== 'none' ? calcNextRetry(sub.retry_policy, 1) : null;

    await db.prepare(
      `UPDATE webhook_deliveries_v3 SET
       status = ?, attempt_count = 1, last_attempt_at = ?, next_retry_at = ?,
       response_status = ?, response_body = ?, duration_ms = ?
       WHERE id = ?`
    ).bind(status, now(), nextRetry, responseStatus, responseBody, duration, deliveryId).run();

    deliveryIds.push(deliveryId);
  }

  return { triggered: matching.length, deliveryIds };
}

export async function getDeliveries(
  db: D1Database, tenantId: string, subId?: string, limit = 50
): Promise<DeliveryRow[]> {
  const cap = Math.min(limit, 200);
  if (subId) {
    const rows = await db.prepare(
      'SELECT * FROM webhook_deliveries_v3 WHERE tenant_id = ? AND subscription_id = ? ORDER BY created_at DESC LIMIT ?'
    ).bind(tenantId, subId, cap).all<DeliveryRow>();
    return rows.results ?? [];
  }
  const rows = await db.prepare(
    'SELECT * FROM webhook_deliveries_v3 WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
  ).bind(tenantId, cap).all<DeliveryRow>();
  return rows.results ?? [];
}

export async function retryDelivery(db: D1Database, tenantId: string, deliveryId: string): Promise<{ queued: boolean }> {
  const delivery = await db.prepare(
    'SELECT * FROM webhook_deliveries_v3 WHERE id = ? AND tenant_id = ?'
  ).bind(deliveryId, tenantId).first<DeliveryRow>();
  if (!delivery || delivery.status === 'delivered') return { queued: false };

  const sub = await db.prepare(
    'SELECT * FROM webhook_subscriptions_v3 WHERE id = ?'
  ).bind(delivery.subscription_id).first<SubscriptionRow>();
  if (!sub) return { queued: false };

  if (delivery.attempt_count >= sub.max_retries) return { queued: false };

  // Reset to retrying so cron can pick it up immediately
  await db.prepare(
    `UPDATE webhook_deliveries_v3 SET status = 'retrying', next_retry_at = ? WHERE id = ?`
  ).bind(now(), deliveryId).run();
  return { queued: true };
}

export async function getDeliveryStats(db: D1Database, tenantId: string) {
  const row = await db.prepare(
    `SELECT
       COUNT(*) as total,
       SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
       SUM(CASE WHEN status IN ('pending','retrying') THEN 1 ELSE 0 END) as pending,
       AVG(duration_ms) as avg_duration_ms
     FROM webhook_deliveries_v3 WHERE tenant_id = ?`
  ).bind(tenantId).first<{ total: number; delivered: number; failed: number; pending: number; avg_duration_ms: number }>();
  return {
    total: row?.total ?? 0,
    delivered: row?.delivered ?? 0,
    failed: row?.failed ?? 0,
    pending: row?.pending ?? 0,
    success_rate: row?.total ? Math.round(((row.delivered ?? 0) / row.total) * 100) : 0,
    avg_duration_ms: Math.round(row?.avg_duration_ms ?? 0),
  };
}

export async function getAdminWebhookOverview(db: D1Database) {
  const subStats = await db.prepare(
    'SELECT COUNT(*) as total_subs, SUM(is_active) as active_subs FROM webhook_subscriptions_v3'
  ).first<{ total_subs: number; active_subs: number }>();
  const delStats = await db.prepare(
    `SELECT
       COUNT(*) as total,
       SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
       SUM(CASE WHEN status IN ('pending','retrying') THEN 1 ELSE 0 END) as pending
     FROM webhook_deliveries_v3`
  ).first<{ total: number; delivered: number; failed: number; pending: number }>();
  return {
    subscriptions: { total: subStats?.total_subs ?? 0, active: subStats?.active_subs ?? 0 },
    deliveries: {
      total: delStats?.total ?? 0,
      delivered: delStats?.delivered ?? 0,
      failed: delStats?.failed ?? 0,
      pending: delStats?.pending ?? 0,
      success_rate: delStats?.total ? Math.round(((delStats.delivered ?? 0) / delStats.total) * 100) : 0,
    },
  };
}
