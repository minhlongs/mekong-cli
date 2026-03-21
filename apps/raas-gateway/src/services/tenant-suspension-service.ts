/**
 * Tenant Suspension Service — manages account suspension lifecycle and payment retries
 * Caches suspension status in KV for fast lookup; D1 as source of truth
 */

import type { Env } from '../index';

// Exponential backoff retry schedule in hours
const RETRY_BACKOFF_HOURS = [1, 4, 12, 24, 72];
const KV_TTL_SECONDS = 3600; // 1h cache TTL

export interface SuspensionRecord {
  id: string;
  tenant_id: string;
  reason: string;
  suspended_at: string;
  grace_period_ends: string | null;
  auto_resume_on_payment: number;
  suspended_by: string;
}

export interface RetryRecord {
  id: string;
  tenant_id: string;
  attempt_number: number;
  status: string;
  error_message: string | null;
  created_at: string;
  next_retry_at: string | null;
}

export class TenantSuspensionService {
  constructor(private env: Env) {}

  /** Suspend a tenant — creates suspension record with optional grace period */
  async suspend(
    tenantId: string,
    reason: string,
    graceDays?: number,
    suspendedBy = 'system'
  ): Promise<SuspensionRecord> {
    const id = crypto.randomUUID();
    const gracePeriodEnds = graceDays
      ? new Date(Date.now() + graceDays * 86400_000).toISOString()
      : null;

    await this.env.DB.prepare(
      `INSERT OR REPLACE INTO tenant_suspensions
       (id, tenant_id, reason, grace_period_ends, auto_resume_on_payment, suspended_by)
       VALUES (?, ?, ?, ?, 1, ?)`
    ).bind(id, tenantId, reason, gracePeriodEnds, suspendedBy).run();

    // Cache suspended state in KV
    await this.env.RATE_LIMIT_KV.put(
      `suspended:${tenantId}`,
      '1',
      { expirationTtl: KV_TTL_SECONDS }
    );

    return {
      id,
      tenant_id: tenantId,
      reason,
      suspended_at: new Date().toISOString(),
      grace_period_ends: gracePeriodEnds,
      auto_resume_on_payment: 1,
      suspended_by: suspendedBy,
    };
  }

  /** Resume a suspended tenant — removes suspension record and clears KV cache */
  async resume(tenantId: string): Promise<boolean> {
    const result = await this.env.DB.prepare(
      'DELETE FROM tenant_suspensions WHERE tenant_id = ?'
    ).bind(tenantId).run();

    await this.env.RATE_LIMIT_KV.delete(`suspended:${tenantId}`);
    return (result.meta.changes ?? 0) > 0;
  }

  /** Check if tenant is suspended — KV fast path, D1 fallback */
  async isSuspended(tenantId: string): Promise<SuspensionRecord | null> {
    // Fast KV check — avoid D1 round-trip on hot path
    const cached = await this.env.RATE_LIMIT_KV.get(`suspended:${tenantId}`);
    if (cached === null) return null; // Not suspended (cache hit)

    // KV had a value — fetch full record from D1 for grace period info
    const record = await this.env.DB.prepare(
      'SELECT * FROM tenant_suspensions WHERE tenant_id = ?'
    ).bind(tenantId).first<SuspensionRecord>();

    if (!record) {
      // KV stale — clear it
      await this.env.RATE_LIMIT_KV.delete(`suspended:${tenantId}`);
      return null;
    }
    return record;
  }

  /** Schedule a payment retry with exponential backoff */
  async scheduleRetry(tenantId: string, attemptNumber: number): Promise<RetryRecord> {
    const id = crypto.randomUUID();
    const backoffHours = RETRY_BACKOFF_HOURS[Math.min(attemptNumber - 1, RETRY_BACKOFF_HOURS.length - 1)];
    const nextRetryAt = new Date(Date.now() + backoffHours * 3_600_000).toISOString();

    await this.env.DB.prepare(
      `INSERT INTO payment_retries (id, tenant_id, attempt_number, status, next_retry_at)
       VALUES (?, ?, ?, 'pending', ?)`
    ).bind(id, tenantId, attemptNumber, nextRetryAt).run();

    return { id, tenant_id: tenantId, attempt_number: attemptNumber, status: 'pending', error_message: null, created_at: new Date().toISOString(), next_retry_at: nextRetryAt };
  }

  /** List all payment retry attempts for a tenant */
  async getRetryHistory(tenantId: string): Promise<RetryRecord[]> {
    const { results } = await this.env.DB.prepare(
      'SELECT * FROM payment_retries WHERE tenant_id = ? ORDER BY created_at DESC'
    ).bind(tenantId).all<RetryRecord>();
    return results;
  }
}
