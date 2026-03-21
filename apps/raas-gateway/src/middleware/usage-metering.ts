/**
 * Usage Metering Middleware — tracks API requests in KV (fire-and-forget)
 *
 * KV keys:
 *   usage:{tenantId}:{YYYY-MM-DD}  — daily count, 48h TTL
 *   usage:{tenantId}:{YYYY-MM}     — monthly count, 35d TTL
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';
import { getTenant } from './auth';

/** Get today's date string in UTC: YYYY-MM-DD */
function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Get current month string in UTC: YYYY-MM */
function monthKey(): string {
  return new Date().toISOString().slice(0, 7);
}

/** Increment a KV counter atomically (read-increment-write) */
async function incrementKv(
  kv: KVNamespace,
  key: string,
  ttlSeconds: number
): Promise<number> {
  const current = await kv.get(key);
  const next = (parseInt(current ?? '0', 10) || 0) + 1;
  await kv.put(key, String(next), { expirationTtl: ttlSeconds });
  return next;
}

/**
 * Usage metering middleware factory.
 * Must be applied AFTER auth() so tenant context is available.
 * Fire-and-forget: never blocks the request.
 */
export function usageMetering(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    await next();

    // Non-blocking — run after response is sent
    try {
      const tenant = getTenant(c);
      const { tenantId } = tenant;
      const kv = c.env.RATE_LIMIT_KV;

      const dailyKvKey = `usage:${tenantId}:${todayKey()}`;
      const monthlyKvKey = `usage:${tenantId}:${monthKey()}`;

      // Increment both counters (48h and 35d TTL)
      const [daily, monthly] = await Promise.all([
        incrementKv(kv, dailyKvKey, 172800),   // 48 hours
        incrementKv(kv, monthlyKvKey, 3024000), // 35 days
      ]);

      // Fetch quota for limit header (best-effort, no D1 error should bubble up)
      let dailyLimit = 1000;
      try {
        const quota = await c.env.DB
          .prepare('SELECT daily_limit FROM usage_quotas WHERE tenant_id = ?')
          .bind(tenantId)
          .first<{ daily_limit: number }>();
        if (quota) dailyLimit = quota.daily_limit;
      } catch { /* quota table may not exist yet */ }

      c.header('X-Usage-Daily', String(daily));
      c.header('X-Usage-Monthly', String(monthly));
      c.header('X-Usage-Limit', String(dailyLimit));

      // Persist record to D1 (best-effort, non-blocking)
      c.executionCtx?.waitUntil(
        c.env.DB.prepare(
          `INSERT INTO usage_records (id, tenant_id, endpoint, method, status_code, credits_consumed, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))`
        )
          .bind(
            crypto.randomUUID(),
            tenantId,
            c.req.path,
            c.req.method,
            c.res.status,
            0
          )
          .run()
          .catch(() => {}) // silent — table may not exist in all envs
      );
    } catch {
      // Never let metering errors surface to caller
    }
  };
}
