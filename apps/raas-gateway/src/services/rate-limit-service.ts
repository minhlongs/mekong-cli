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
  remaining: number;
  resetAt: number;       // Unix timestamp (seconds)
  retryAfter?: number;   // Seconds until token available
}

// Rate limits by tier (requests per minute)
const TIER_LIMITS: Record<string, RateLimitConfig> = {
  starter: { capacity: 100, refillRate: 100 / 60 },    // ~1.67/sec
  pro: { capacity: 500, refillRate: 500 / 60 },        // ~8.33/sec
  enterprise: { capacity: 2000, refillRate: 2000 / 60 }, // ~33.33/sec
};

export class RateLimitService {
  constructor(private env: Env) {}

  /**
   * Get rate limit config for tier
   */
  private getConfig(tier: string): RateLimitConfig {
    return TIER_LIMITS[tier] || TIER_LIMITS.starter;
  }

  /**
   * KV key for tenant rate limit bucket
   */
  private getKey(tenantId: string): string {
    return `ratelimit:${tenantId}`;
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
    const key = this.getKey(tenantId);
    const now = Date.now();

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

        // Persist updated bucket
        await this.env.RATE_LIMIT_KV.put(
          key,
          JSON.stringify({ tokens, lastRefill }),
          { expirationTtl: 120 } // Auto-expire after 2 min inactivity
        );

        return {
          allowed: true,
          remaining: Math.floor(tokens),
          resetAt: Math.ceil(now / 1000) + 60, // Full refill in ~60s
        };
      } else {
        // Rate limited - calculate retry time
        const tokensNeeded = 1 - tokens;
        const retryAfter = Math.ceil(tokensNeeded / config.refillRate);
        const resetAt = Math.ceil((lastRefill / 1000) + (config.capacity / config.refillRate));

        return {
          allowed: false,
          remaining: 0,
          resetAt,
          retryAfter,
        };
      }
    } catch (error) {
      console.error('[RateLimitService] Error checking limit:', error);
      // Fail open - allow request if KV fails
      return {
        allowed: true,
        remaining: config.capacity,
        resetAt: Math.ceil(now / 1000) + 60,
      };
    }
  }

  /**
   * Get current rate limit status (without consuming)
   */
  async getStatus(tenantId: string, tier: string): Promise<RateLimitResult> {
    const config = this.getConfig(tier);
    const key = this.getKey(tenantId);
    const now = Date.now();

    try {
      const bucketData = await this.env.RATE_LIMIT_KV.get(key, 'json') as {
        tokens: number;
        lastRefill: number;
      } | null;

      if (!bucketData) {
        return {
          allowed: true,
          remaining: config.capacity,
          resetAt: Math.ceil(now / 1000) + 60,
        };
      }

      const elapsed = (now - bucketData.lastRefill) / 1000;
      const tokens = Math.min(
        config.capacity,
        bucketData.tokens + (elapsed * config.refillRate)
      );

      return {
        allowed: tokens >= 1,
        remaining: Math.floor(tokens),
        resetAt: Math.ceil(now / 1000) + 60,
      };
    } catch (error) {
      console.error('[RateLimitService] Error getting status:', error);
      return {
        allowed: true,
        remaining: config.capacity,
        resetAt: Math.ceil(now / 1000) + 60,
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
