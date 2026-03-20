/**
 * Tenant Rate Limit Configuration
 * Per-tier rate limits for RaaS Gateway
 */

export type TenantTier = 'free' | 'starter' | 'pro' | 'enterprise'

export interface RateLimitConfig {
  requestsPerHour: number
  requestsPerDay: number
}

/**
 * Rate limits per tenant tier
 * Free: 50/hour, 500/day
 * Starter: 100/hour, 2,000/day
 * Pro: 500/hour, 10,000/day
 * Enterprise: 2,000/hour, 50,000/day
 */
export const TIER_LIMITS: Record<TenantTier, RateLimitConfig> = {
  free: {
    requestsPerHour: 50,
    requestsPerDay: 500,
  },
  starter: {
    requestsPerHour: 100,
    requestsPerDay: 2000,
  },
  pro: {
    requestsPerHour: 500,
    requestsPerDay: 10000,
  },
  enterprise: {
    requestsPerHour: 2000,
    requestsPerDay: 50000,
  },
}

/**
 * Get rate limit config for a given tier
 */
export function getRateLimitConfig(tier: TenantTier): RateLimitConfig {
  return TIER_LIMITS[tier] || TIER_LIMITS.free
}

/**
 * Calculate retry-after seconds based on window type
 * hour = 3600s, day = 86400s
 */
export function getRetryAfterSeconds(window: 'hour' | 'day'): number {
  return window === 'hour' ? 3600 : 86400
}

/**
 * Get window key prefix for KV storage
 */
export function getWindowKey(tenantId: string, window: 'hour' | 'day'): string {
  const now = new Date()
  const hourKey = `rate:${tenantId}:hour:${now.getUTCHours()}`
  const dayKey = `rate:${tenantId}:day:${now.getUTCDate()}`
  return window === 'hour' ? hourKey : dayKey
}
