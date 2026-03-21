/**
 * Rate Limit Service — Token Bucket algorithm using KV storage
 */

import type { Env } from '../index';

export interface RateLimitConfig {
  capacity: number;      // Max tokens (requests per minute)
  refillRate: number;    // Tokens added per second
}

export interface RateLimitResult {
  allowed: boolean;
  limit: number;         // Max requests per minute for this tier
  remaining: number;
  resetAt: number;       // Unix timestamp (seconds)
  retryAfter?: number;   // Seconds until token available
}

// Requests per minute by tier
const TIER_RATE_LIMITS: Record<string, number> = {
  free: 10,
  starter: 30,
  pro: 60,
  agency: 120,
  master: 300,
  enterprise: 1000,
};

// Token bucket config derived from per-minute limits
function tierConfig(rpm: number): RateLimitConfig {
  return { capacity: rpm, refillRate: rpm / 60 };
}

export class RateLimitService {
  constructor(private env: Env) {}

  /**
   * Get rate limit config for tier — defaults to free if unknown
   */
  private getConfig(tier: string): RateLimitConfig {
    const rpm = TIER_RATE_LIMITS[tier] ?? TIER_RATE_LIMITS.free;
    return tierConfig(rpm);
  }

  /**
   * Get requests-per-minute limit for tier
   */
  getLimit(tier: string): number {
    return TIER_RATE_LIMITS[tier] ?? TIER_RATE_LIMITS.free;
  }

  /**
   * KV key per tenant per minute window
   * Format: rl:{tenantId}:{minute}
   */
  private getKey(tenantId: string): string {
    const minute = Math.floor(Date.now() / 60_000);
    return `rl:${tenantId}:${minute}`;
  }

  /**
   * Check and consume rate limit using token bucket algorithm
   *
   * Token Bucket:
   * - Bucket starts full (capacity tokens)
   * - Each request consumes 1 token
   * - Tokens refill continuously at refillRate per second
   * - Requests denied when bucket empty
   */
  async checkLimit(tenantId: string, tier: string): Promise<RateLimitResult> {
    const config = this.getConfig(tier);
    const limit = this.getLimit(tier);
    const key = this.getKey(tenantId);
    const now = Date.now();
    // Reset timestamp = start of next minute window
    const nextMinute = (Math.floor(now / 60_000) + 1) * 60;

    try {
      // Get current bucket state from KV
      const bucketData = await this.env.RATE_LIMIT_KV.get(key, 'json') as {
        tokens: number;
        lastRefill: number;
      } | null;

      let tokens: number;
      let lastRefill: number;

      if (bucketData) {
        // Calculate tokens since last refill
        const elapsed = (now - bucketData.lastRefill) / 1000; // seconds
        tokens = Math.min(
          config.capacity,
          bucketData.tokens + (elapsed * config.refillRate)
        );
        lastRefill = now;
      } else {
        // New bucket starts full
        tokens = config.capacity;
        lastRefill = now;
      }

      // Check if request allowed
      if (tokens >= 1) {
        // Consume 1 token
        tokens -= 1;

        // Persist updated bucket — TTL 90s covers current + next minute window
        await this.env.RATE_LIMIT_KV.put(
          key,
          JSON.stringify({ tokens, lastRefill }),
          { expirationTtl: 90 }
        );

        return {
          allowed: true,
          limit,
          remaining: Math.floor(tokens),
          resetAt: nextMinute,
        };
      } else {
        // Rate limited — retry after next minute window starts
        const tokensNeeded = 1 - tokens;
        const retryAfter = Math.ceil(tokensNeeded / config.refillRate);

        return {
          allowed: false,
          limit,
          remaining: 0,
          resetAt: nextMinute,
          retryAfter,
        };
      }
    } catch (error) {
      console.error('[RateLimitService] Error checking limit:', error);
      // Fail open — allow request if KV unavailable
      return {
        allowed: true,
        limit,
        remaining: config.capacity,
        resetAt: nextMinute,
      };
    }
  }

  /**
   * Get current rate limit status (without consuming a token)
   */
  async getStatus(tenantId: string, tier: string): Promise<RateLimitResult> {
    const config = this.getConfig(tier);
    const limit = this.getLimit(tier);
    const key = this.getKey(tenantId);
    const now = Date.now();
    const nextMinute = (Math.floor(now / 60_000) + 1) * 60;

    try {
      const bucketData = await this.env.RATE_LIMIT_KV.get(key, 'json') as {
        tokens: number;
        lastRefill: number;
      } | null;

      if (!bucketData) {
        return {
          allowed: true,
          limit,
          remaining: config.capacity,
          resetAt: nextMinute,
        };
      }

      const elapsed = (now - bucketData.lastRefill) / 1000;
      const tokens = Math.min(
        config.capacity,
        bucketData.tokens + (elapsed * config.refillRate)
      );

      return {
        allowed: tokens >= 1,
        limit,
        remaining: Math.floor(tokens),
        resetAt: nextMinute,
      };
    } catch (error) {
      console.error('[RateLimitService] Error getting status:', error);
      return {
        allowed: true,
        limit,
        remaining: config.capacity,
        resetAt: nextMinute,
      };
    }
  }

  /**
   * Reset rate limit for tenant (admin operation)
   */
  async reset(tenantId: string): Promise<void> {
    const key = this.getKey(tenantId);
    await this.env.RATE_LIMIT_KV.delete(key);
  }
}
