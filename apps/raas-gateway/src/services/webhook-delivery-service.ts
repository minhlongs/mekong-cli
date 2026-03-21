/**
 * Webhook Delivery Service — queues and retries webhook deliveries with exponential backoff.
 * Dead letter queue for max-attempts-exceeded deliveries.
 */

import type { Env } from '../index';

// Retry delays in seconds: 1min, 5min, 30min
const RETRY_DELAYS = [60, 300, 1800];

export class WebhookDeliveryService {
  constructor(private env: Env) {}

  /** Queue a new webhook delivery record, returns delivery id */
  async queueDelivery(
    tenantId: string,
    eventType: string,
    payload: object,
    url: string,
  ): Promise<string> {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await this.env.DB.prepare(
      `INSERT INTO webhook_delivery_logs
        (id, tenant_id, event_type, payload, url, status, attempts, max_attempts, created_at)
       VALUES (?, ?, ?, ?, ?, 'pending', 0, 3, ?)`,
    )
      .bind(id, tenantId, eventType, JSON.stringify(payload), url, now)
      .run();
    return id;
  }

  /** Attempt HTTP delivery; on failure schedule retry or mark dead letter. Returns success flag. */
  async attemptDelivery(deliveryId: string): Promise<boolean> {
    const row = await this.env.DB.prepare(
      'SELECT * FROM webhook_delivery_logs WHERE id = ?',
    )
      .bind(deliveryId)
      .first<Record<string, any>>();

    if (!row) return false;

    const now = new Date().toISOString();
    const attempt = (row.attempts as number) + 1;
    let httpStatus: number | null = null;
    let responseBody: string | null = null;
    let success = false;

    try {
      const res = await fetch(row.url as string, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Mekong-Event': row.event_type as string },
        body: row.payload as string,
        signal: AbortSignal.timeout(10_000),
      });
      httpStatus = res.status;
      responseBody = (await res.text()).slice(0, 500);
      success = res.ok;
    } catch (err) {
      console.error(`[WebhookDelivery] fetch error id=${deliveryId}:`, err);
      responseBody = err instanceof Error ? err.message : 'Unknown error';
    }

    if (success) {
      await this.env.DB.prepare(
        `UPDATE webhook_delivery_logs
         SET status='delivered', http_status=?, response_body=?, attempts=?, last_attempted_at=?
         WHERE id=?`,
      )
        .bind(httpStatus, responseBody, attempt, now, deliveryId)
        .run();
      return true;
    }

    // Determine next status
    const maxAttempts = row.max_attempts as number;
    if (attempt >= maxAttempts) {
      await this.markDeadLetter(deliveryId, attempt, httpStatus, responseBody, now);
    } else {
      const delaySec = RETRY_DELAYS[attempt - 1] ?? RETRY_DELAYS[RETRY_DELAYS.length - 1];
      const nextRetry = new Date(Date.now() + delaySec * 1000).toISOString();
      await this.env.DB.prepare(
        `UPDATE webhook_delivery_logs
         SET status='retry', http_status=?, response_body=?, attempts=?, last_attempted_at=?, next_retry_at=?
         WHERE id=?`,
      )
        .bind(httpStatus, responseBody, attempt, now, nextRetry, deliveryId)
        .run();
    }
    return false;
  }

  /** Return pending retry records due for re-attempt */
  async getPendingRetries(limit = 50): Promise<any[]> {
    const now = new Date().toISOString();
    const result = await this.env.DB.prepare(
      `SELECT * FROM webhook_delivery_logs
       WHERE status = 'retry' AND next_retry_at <= ?
       ORDER BY next_retry_at ASC LIMIT ?`,
    )
      .bind(now, limit)
      .all();
    return result.results;
  }

  /** Mark delivery as dead_letter after max attempts exhausted */
  private async markDeadLetter(
    deliveryId: string,
    attempts: number,
    httpStatus: number | null,
    responseBody: string | null,
    now: string,
  ): Promise<void> {
    await this.env.DB.prepare(
      `UPDATE webhook_delivery_logs
       SET status='dead_letter', http_status=?, response_body=?, attempts=?, last_attempted_at=?
       WHERE id=?`,
    )
      .bind(httpStatus, responseBody, attempts, now, deliveryId)
      .run();
  }
}
