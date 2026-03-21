/**
 * Webhook Retry Service — processes failed deliveries and manages dead letter queue.
 * Exponential backoff: 1m → 5m → 30m → 2h → 12h
 */

import type { D1Database, KVNamespace } from '@cloudflare/workers-types';

// Retry delay schedule in seconds
const RETRY_DELAYS_SEC = [60, 300, 1800, 7200, 43200];
const MAX_ATTEMPTS = 5;

export interface DLQStats {
  total_unresolved: number;
  total_resolved: number;
  by_event_type: Array<{ event_type: string; count: number }>;
}

interface DeliveryRow {
  id: string;
  webhook_id: string;
  tenant_id: string;
  event_type: string;
  payload: string;
  url: string;
  attempts: number;
  http_status: number | null;
  response_body: string | null;
}

interface DLQRow {
  id: number;
  delivery_id: string;
  webhook_id: string;
  tenant_id: string;
  event_type: string;
  payload: string;
  url?: string;
}

export class WebhookRetryService {
  /**
   * Find failed deliveries due for retry; move exhausted ones to DLQ.
   */
  async processRetries(
    db: D1Database,
    _kv: KVNamespace,
  ): Promise<{ retried: number; moved_to_dlq: number }> {
    const now = new Date().toISOString();

    const { results } = await db
      .prepare(
        `SELECT * FROM webhook_delivery_logs
         WHERE status = 'retry' AND next_retry_at <= ? AND attempts < ?
         ORDER BY next_retry_at ASC LIMIT 50`,
      )
      .bind(now, MAX_ATTEMPTS)
      .all<DeliveryRow>();

    let retried = 0;
    let moved_to_dlq = 0;

    for (const delivery of results) {
      if (delivery.attempts >= MAX_ATTEMPTS - 1) {
        // This attempt will be the final one — move to DLQ on failure
        const ok = await this.retryDelivery(db, delivery);
        if (!ok) {
          const lastError = delivery.response_body ?? 'Max attempts exceeded';
          await this.moveToDLQ(db, delivery, lastError);
          moved_to_dlq++;
        } else {
          retried++;
        }
      } else {
        const ok = await this.retryDelivery(db, delivery);
        if (ok) retried++;
      }
    }

    return { retried, moved_to_dlq };
  }

  /**
   * Attempt HTTP POST to webhook URL; update delivery record.
   * Returns true on 2xx response.
   */
  async retryDelivery(db: D1Database, delivery: DeliveryRow): Promise<boolean> {
    const attempt = delivery.attempts + 1;
    const now = new Date().toISOString();
    let httpStatus: number | null = null;
    let responseBody: string | null = null;
    let success = false;

    try {
      const res = await fetch(delivery.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Mekong-Event': delivery.event_type,
          'X-Webhook-Attempt': String(attempt),
        },
        body: delivery.payload,
        signal: AbortSignal.timeout(10_000),
      });
      httpStatus = res.status;
      responseBody = (await res.text()).slice(0, 500);
      success = res.ok;
    } catch (err) {
      responseBody = err instanceof Error ? err.message : 'fetch error';
    }

    if (success) {
      await db
        .prepare(
          `UPDATE webhook_delivery_logs
           SET status='delivered', http_status=?, response_body=?, attempts=?, last_attempted_at=?
           WHERE id=?`,
        )
        .bind(httpStatus, responseBody, attempt, now, delivery.id)
        .run();
      return true;
    }

    // Schedule next retry or mark exhausted
    const delaySec = RETRY_DELAYS_SEC[attempt - 1] ?? RETRY_DELAYS_SEC[RETRY_DELAYS_SEC.length - 1];
    const nextRetry = new Date(Date.now() + delaySec * 1000).toISOString();
    const nextStatus = attempt >= MAX_ATTEMPTS ? 'dead_letter' : 'retry';

    await db
      .prepare(
        `UPDATE webhook_delivery_logs
         SET status=?, http_status=?, response_body=?, attempts=?, last_attempted_at=?, next_retry_at=?
         WHERE id=?`,
      )
      .bind(nextStatus, httpStatus, responseBody, attempt, now, nextRetry, delivery.id)
      .run();

    return false;
  }

  /**
   * Insert delivery into dead letter table; mark original as 'dead_letter'.
   */
  async moveToDLQ(db: D1Database, delivery: DeliveryRow, error: string): Promise<void> {
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO webhook_dead_letters
           (delivery_id, webhook_id, tenant_id, event_type, payload, last_error,
            last_status_code, total_attempts, moved_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      )
      .bind(
        delivery.id,
        delivery.webhook_id ?? delivery.id,
        delivery.tenant_id,
        delivery.event_type,
        delivery.payload,
        error,
        delivery.http_status,
        delivery.attempts,
        now,
      )
      .run();

    await db
      .prepare(`UPDATE webhook_delivery_logs SET status='dead_letter' WHERE id=?`)
      .bind(delivery.id)
      .run();
  }

  /**
   * Create a new delivery from a DLQ entry and mark DLQ entry as resolved.
   */
  async replayFromDLQ(db: D1Database, dlqId: number): Promise<{ success: boolean }> {
    const row = await db
      .prepare(`SELECT * FROM webhook_dead_letters WHERE id = ?`)
      .bind(dlqId)
      .first<DLQRow>();

    if (!row) return { success: false };

    // Fetch original delivery url
    const original = await db
      .prepare(`SELECT url FROM webhook_delivery_logs WHERE id = ?`)
      .bind(row.delivery_id)
      .first<{ url: string }>();

    if (!original?.url) return { success: false };

    const newId = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO webhook_delivery_logs
           (id, tenant_id, event_type, payload, url, status, attempts, max_attempts, created_at)
         VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)`,
      )
      .bind(newId, row.tenant_id, row.event_type, row.payload, original.url, MAX_ATTEMPTS, now)
      .run();

    await db
      .prepare(
        `UPDATE webhook_dead_letters SET resolved_at=?, resolution='replayed' WHERE id=?`,
      )
      .bind(now, dlqId)
      .run();

    return { success: true };
  }

  /**
   * Aggregate DLQ counts by event type and resolution status.
   */
  async getDLQStats(db: D1Database, tenantId?: string): Promise<DLQStats> {
    // Build optional tenant clause — appended with AND since base WHERE is always present
    const tenantClause = tenantId ? 'AND tenant_id = ?' : '';
    const bind = tenantId ? [tenantId] : [];

    const unresolvedResult = await db
      .prepare(
        `SELECT COUNT(*) as count FROM webhook_dead_letters
         WHERE resolved_at IS NULL ${tenantClause}`,
      )
      .bind(...bind)
      .first<{ count: number }>();

    const resolvedResult = await db
      .prepare(
        `SELECT COUNT(*) as count FROM webhook_dead_letters
         WHERE resolved_at IS NOT NULL ${tenantClause}`,
      )
      .bind(...bind)
      .first<{ count: number }>();

    const byEventType = await db
      .prepare(
        `SELECT event_type, COUNT(*) as count FROM webhook_dead_letters
         WHERE 1=1 ${tenantClause}
         GROUP BY event_type ORDER BY count DESC`,
      )
      .bind(...bind)
      .all<{ event_type: string; count: number }>();

    return {
      total_unresolved: unresolvedResult?.count ?? 0,
      total_resolved: resolvedResult?.count ?? 0,
      by_event_type: byEventType.results,
    };
  }
}
