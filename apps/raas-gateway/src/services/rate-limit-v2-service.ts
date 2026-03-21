/**
 * Adaptive Rate Limiting v2 — Token Bucket with Burst + Cooldown
 *
 * Algorithm:
 *  - Each tenant has a token bucket in KV: { tokens, last_refill, cooldown_until }
 *  - Tokens refill at rate = requests_per_minute / 60 per second
 *  - Burst allowance adds extra capacity on top of base tokens
 *  - On limit hit: apply cooldown penalty, record event in D1
 */

export interface RateLimitConfig {
  requests_per_minute: number;
  burst_allowance: number;
  cooldown_seconds: number;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  reset_at: number;        // Unix seconds
  retry_after?: number;    // Seconds until allowed (only when blocked)
  limit: number;
}

interface BucketState {
  tokens: number;
  last_refill: number;     // Unix ms
  cooldown_until: number;  // Unix ms, 0 = no cooldown
}

// ---------------------------------------------------------------------------
// Tier defaults
// ---------------------------------------------------------------------------

export const TIER_LIMITS: Record<string, RateLimitConfig> = {
  starter:    { requests_per_minute: 60,   burst_allowance: 10,  cooldown_seconds: 60 },
  pro:        { requests_per_minute: 300,  burst_allowance: 50,  cooldown_seconds: 30 },
  agency:     { requests_per_minute: 600,  burst_allowance: 100, cooldown_seconds: 15 },
  master:     { requests_per_minute: 1200, burst_allowance: 200, cooldown_seconds: 10 },
  enterprise: { requests_per_minute: 3000, burst_allowance: 500, cooldown_seconds: 5  },
};

const FALLBACK_CONFIG: RateLimitConfig = TIER_LIMITS.starter;

// ---------------------------------------------------------------------------
// KV helpers
// ---------------------------------------------------------------------------

const bucketKey = (tenantId: string) => `rl2:bucket:${tenantId}`;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Token bucket check. Consumes one token if allowed.
 * Returns headers-ready result.
 */
export async function checkRateLimit(
  kv: KVNamespace,
  tenantId: string,
  tier: string,
  config?: RateLimitConfig,
): Promise<RateLimitResult> {
  const cfg = config ?? TIER_LIMITS[tier] ?? FALLBACK_CONFIG;
  const capacity = cfg.requests_per_minute + cfg.burst_allowance;
  const refillPerMs = cfg.requests_per_minute / 60000; // tokens per ms
  const now = Date.now();

  const raw = await kv.get<BucketState>(bucketKey(tenantId), 'json');
  const state: BucketState = raw ?? { tokens: capacity, last_refill: now, cooldown_until: 0 };

  // Check active cooldown
  if (state.cooldown_until > now) {
    const retry_after = Math.ceil((state.cooldown_until - now) / 1000);
    return {
      allowed: false,
      remaining: 0,
      reset_at: Math.ceil(state.cooldown_until / 1000),
      retry_after,
      limit: cfg.requests_per_minute,
    };
  }

  // Refill tokens based on elapsed time
  const elapsed = now - state.last_refill;
  const refilled = Math.min(capacity, state.tokens + elapsed * refillPerMs);

  if (refilled < 1) {
    // Out of tokens — apply cooldown
    const cooldown_until = now + cfg.cooldown_seconds * 1000;
    await kv.put(
      bucketKey(tenantId),
      JSON.stringify({ ...state, tokens: 0, last_refill: now, cooldown_until }),
      { expirationTtl: cfg.cooldown_seconds + 120 },
    );
    return {
      allowed: false,
      remaining: 0,
      reset_at: Math.ceil(cooldown_until / 1000),
      retry_after: cfg.cooldown_seconds,
      limit: cfg.requests_per_minute,
    };
  }

  // Consume one token
  const newTokens = refilled - 1;
  const reset_at = Math.ceil(now / 1000) + Math.ceil((capacity - newTokens) / (refillPerMs * 1000));
  await kv.put(
    bucketKey(tenantId),
    JSON.stringify({ tokens: newTokens, last_refill: now, cooldown_until: 0 }),
    { expirationTtl: 3600 },
  );

  return {
    allowed: true,
    remaining: Math.floor(newTokens),
    reset_at,
    limit: cfg.requests_per_minute,
  };
}

/** Current bucket state without consuming a token */
export async function getRateLimitStatus(kv: KVNamespace, tenantId: string): Promise<BucketState | null> {
  return kv.get<BucketState>(bucketKey(tenantId), 'json');
}

/** Persist custom config override for a tenant in D1 */
export async function setCustomLimit(
  db: D1Database,
  tenantId: string,
  config: Partial<RateLimitConfig>,
): Promise<void> {
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO rate_limit_configs (id, tenant_id, requests_per_minute, burst_allowance, cooldown_seconds, updated_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(tenant_id) DO UPDATE SET
         requests_per_minute = COALESCE(excluded.requests_per_minute, requests_per_minute),
         burst_allowance      = COALESCE(excluded.burst_allowance, burst_allowance),
         cooldown_seconds     = COALESCE(excluded.cooldown_seconds, cooldown_seconds),
         updated_at           = datetime('now')`,
    )
    .bind(
      id,
      tenantId,
      config.requests_per_minute ?? null,
      config.burst_allowance ?? null,
      config.cooldown_seconds ?? null,
    )
    .run();
}

/** Get custom config from D1, or null if not set */
export async function getCustomLimit(
  db: D1Database,
  tenantId: string,
  tier: string,
): Promise<RateLimitConfig> {
  const row = await db
    .prepare('SELECT requests_per_minute, burst_allowance, cooldown_seconds FROM rate_limit_configs WHERE tenant_id = ?')
    .bind(tenantId)
    .first<RateLimitConfig>();
  return row ?? TIER_LIMITS[tier] ?? FALLBACK_CONFIG;
}

/** Rate limit event history for a tenant */
export async function getRateLimitHistory(
  db: D1Database,
  tenantId: string,
  hours = 24,
): Promise<Record<string, unknown>[]> {
  const since = new Date(Date.now() - hours * 3600 * 1000).toISOString();
  const { results } = await db
    .prepare(
      'SELECT id, endpoint, status_code, created_at FROM rate_limit_events WHERE tenant_id = ? AND created_at > ? ORDER BY created_at DESC LIMIT 200',
    )
    .bind(tenantId, since)
    .all();
  return results as Record<string, unknown>[];
}

/** Record a rate limit hit event for analytics */
export async function recordLimitHit(
  db: D1Database,
  tenantId: string,
  endpoint: string,
  statusCode: number,
): Promise<void> {
  await db
    .prepare('INSERT INTO rate_limit_events (id, tenant_id, endpoint, status_code) VALUES (?, ?, ?, ?)')
    .bind(crypto.randomUUID(), tenantId, endpoint, statusCode)
    .run();
}

/** Top rate-limited tenants for admin analytics */
export async function getTopRateLimitedTenants(
  db: D1Database,
  hours = 24,
  limit = 10,
): Promise<Record<string, unknown>[]> {
  const since = new Date(Date.now() - hours * 3600 * 1000).toISOString();
  const { results } = await db
    .prepare(
      `SELECT tenant_id, COUNT(*) as hit_count, MAX(created_at) as last_hit
       FROM rate_limit_events
       WHERE created_at > ?
       GROUP BY tenant_id
       ORDER BY hit_count DESC
       LIMIT ?`,
    )
    .bind(since, limit)
    .all();
  return results as Record<string, unknown>[];
}
