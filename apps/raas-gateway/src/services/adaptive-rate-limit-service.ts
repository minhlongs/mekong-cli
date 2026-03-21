/**
 * Adaptive Rate Limit Service — Tenant-aware sliding window + tier quota management
 *
 * Strategy: sliding_window counters in KV (minute + hour buckets)
 * Violations + adaptation logic → adaptive-rate-limit-violations.ts
 */

import type { Env } from '../index';

export interface TierDefaults {
  tier: string;
  requests_per_minute: number;
  requests_per_hour: number;
  daily_limit: number;
  burst_allowance: number;
  concurrent_limit: number;
}

export interface RateLimitConfig {
  endpoint_pattern: string;
  requests_per_minute: number;
  requests_per_hour: number;
  burst_allowance: number;
  throttle_strategy: string;
  is_active: number;
}

export interface CheckResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;    // Unix seconds
  retryAfter?: number;
}

// Re-export violation helpers so routes import from one place
export {
  recordViolation,
  getViolationHistory,
  getTopViolators,
  adaptLimits,
} from './adaptive-rate-limit-violations';

// KV sliding-window counter keys (minute + hour buckets)
const kvMinuteKey = (tenantId: string, endpoint: string) =>
  `arl:min:${tenantId}:${endpoint}:${Math.floor(Date.now() / 60000)}`;
const kvHourKey = (tenantId: string, endpoint: string) =>
  `arl:hr:${tenantId}:${endpoint}:${Math.floor(Date.now() / 3600000)}`;

// ---------------------------------------------------------------------------
// Tier defaults
// ---------------------------------------------------------------------------

export async function getTierDefaults(db: D1Database, tier: string): Promise<TierDefaults | null> {
  return db
    .prepare('SELECT * FROM tier_rate_defaults WHERE tier = ?')
    .bind(tier)
    .first<TierDefaults>();
}

export async function seedTierDefaults(db: D1Database): Promise<void> {
  const tiers = [
    { tier: 'starter',    rpm: 30,  rph: 500,   daily: 5000,   burst: 5,   concurrent: 2  },
    { tier: 'pro',        rpm: 120, rph: 3000,  daily: 30000,  burst: 20,  concurrent: 10 },
    { tier: 'enterprise', rpm: 600, rph: 20000, daily: 200000, burst: 100, concurrent: 50 },
  ];
  const stmt = db.prepare(
    `INSERT OR REPLACE INTO tier_rate_defaults
     (id, tier, requests_per_minute, requests_per_hour, daily_limit, burst_allowance, concurrent_limit)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  );
  await db.batch(
    tiers.map(t => stmt.bind(crypto.randomUUID(), t.tier, t.rpm, t.rph, t.daily, t.burst, t.concurrent))
  );
}

// ---------------------------------------------------------------------------
// Tenant config management
// ---------------------------------------------------------------------------

export async function setTenantConfig(
  db: D1Database,
  tenantId: string,
  endpointPattern: string,
  config: Partial<Omit<RateLimitConfig, 'endpoint_pattern' | 'is_active'>>
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO rate_limit_configs
         (id, tenant_id, endpoint_pattern, requests_per_minute, requests_per_hour, burst_allowance, throttle_strategy)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(tenant_id, endpoint_pattern) DO UPDATE SET
         requests_per_minute = excluded.requests_per_minute,
         requests_per_hour   = excluded.requests_per_hour,
         burst_allowance     = excluded.burst_allowance,
         throttle_strategy   = excluded.throttle_strategy`
    )
    .bind(
      crypto.randomUUID(),
      tenantId,
      endpointPattern,
      config.requests_per_minute ?? 60,
      config.requests_per_hour   ?? 1000,
      config.burst_allowance     ?? 10,
      config.throttle_strategy   ?? 'sliding_window'
    )
    .run();
}

export async function getTenantConfigs(db: D1Database, tenantId: string): Promise<RateLimitConfig[]> {
  const { results } = await db
    .prepare('SELECT * FROM rate_limit_configs WHERE tenant_id = ? AND is_active = 1')
    .bind(tenantId)
    .all<RateLimitConfig>();
  return results;
}

// ---------------------------------------------------------------------------
// Rate check — sliding window via KV
// ---------------------------------------------------------------------------

export async function checkRateLimit(
  db: D1Database,
  kv: KVNamespace,
  tenantId: string,
  endpoint: string,
  tier: string
): Promise<CheckResult> {
  const tierDef = await getTierDefaults(db, tier);
  const rpm   = tierDef?.requests_per_minute ?? 60;
  const rph   = tierDef?.requests_per_hour   ?? 1000;
  const burst = tierDef?.burst_allowance      ?? 10;
  const limit = rpm + burst;

  const minKey = kvMinuteKey(tenantId, endpoint);
  const hrKey  = kvHourKey(tenantId, endpoint);

  const [minRaw, hrRaw] = await Promise.all([kv.get(minKey), kv.get(hrKey)]);
  const minCount = parseInt(minRaw ?? '0', 10);
  const hrCount  = parseInt(hrRaw  ?? '0', 10);

  const nowSec  = Math.floor(Date.now() / 1000);
  const resetAt = (Math.floor(Date.now() / 60000) + 1) * 60;

  if (minCount >= limit) {
    return { allowed: false, remaining: 0, resetAt, retryAfter: resetAt - nowSec };
  }
  if (hrCount >= rph) {
    const hrResetAt = (Math.floor(Date.now() / 3600000) + 1) * 3600;
    return { allowed: false, remaining: 0, resetAt: hrResetAt, retryAfter: hrResetAt - nowSec };
  }

  await Promise.all([
    kv.put(minKey, String(minCount + 1), { expirationTtl: 120 }),
    kv.put(hrKey,  String(hrCount  + 1), { expirationTtl: 7200 }),
  ]);

  return { allowed: true, remaining: limit - minCount - 1, resetAt };
}

// ---------------------------------------------------------------------------
// Standard rate limit response headers
// ---------------------------------------------------------------------------

export function getRateLimitHeaders(result: CheckResult): Record<string, string> {
  const headers: Record<string, string> = {
    'X-RateLimit-Remaining': String(result.remaining),
    'X-RateLimit-Reset':     String(result.resetAt),
  };
  if (result.retryAfter !== undefined) headers['Retry-After'] = String(result.retryAfter);
  return headers;
}
