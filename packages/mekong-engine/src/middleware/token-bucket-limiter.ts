/**
 * Token Bucket Rate Limiter using Cloudflare KV
 */

import type { KVNamespace } from '@cloudflare/workers-types'
import { getRateLimitConfig, type TenantTier } from '../lib/tenant-limits'
import { logger } from '../lib/monitoring'

export interface RateLimitState {
  count: number
  windowStart: number
}

export interface RateLimitHeaders extends Record<string, string> {
  'X-RateLimit-Limit': string
  'X-RateLimit-Remaining': string
  'X-RateLimit-Reset': string
}

export interface RateLimitExceededResponse {
  error: string
  code: string
  retry_after: number
  limit: number
  remaining: number
  reset: number
}

export class TokenBucketLimiter {
  private kv: KVNamespace

  constructor(kv: KVNamespace) {
    this.kv = kv
  }

  /**
   * Check if request is within rate limit
   * Uses sliding window counter algorithm for accuracy
   */
  async check(
    tenantId: string,
    tier: TenantTier,
    window: 'hour' | 'day'
  ): Promise<{
    allowed: boolean
    limit: number
    remaining: number
    reset: number
    headers: RateLimitHeaders
  }> {
    const config = getRateLimitConfig(tier)
    const maxRequests = window === 'hour' ? config.requestsPerHour : config.requestsPerDay
    const windowMs = window === 'hour' ? 3600000 : 86400000
    const now = Date.now()
    const windowStart = Math.floor(now / windowMs) * windowMs
    const windowEnd = windowStart + windowMs
    const kvKey = this.getKvKey(tenantId, window, windowStart)

    try {
      const stored = (await this.kv.get(kvKey, 'json')) as RateLimitState | null
      const state: RateLimitState =
        !stored || stored.windowStart < windowStart
          ? { count: 0, windowStart }
          : stored

      const remaining = Math.max(0, maxRequests - state.count)
      const reset = Math.ceil(windowEnd / 1000)

      if (state.count >= maxRequests) {
        return {
          allowed: false,
          limit: maxRequests,
          remaining: 0,
          reset,
          headers: {
            'X-RateLimit-Limit': String(maxRequests),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String(reset),
            'Retry-After': String(Math.ceil((windowEnd - now) / 1000)),
          },
        }
      }

      state.count++
      await this.kv.put(kvKey, JSON.stringify(state), {
        expirationTtl: Math.ceil(windowMs / 1000) + 60,
      })

      return {
        allowed: true,
        limit: maxRequests,
        remaining: remaining - 1,
        reset,
        headers: {
          'X-RateLimit-Limit': String(maxRequests),
          'X-RateLimit-Remaining': String(remaining - 1),
          'X-RateLimit-Reset': String(reset),
        },
      }
    } catch (error) {
      logger.error('Rate limit KV operation failed', {
        error: error instanceof Error ? error.message : String(error),
        tenantId,
        window,
      })

      const reset = Math.ceil((windowEnd - now) / 1000)
      return {
        allowed: true,
        limit: maxRequests,
        remaining: maxRequests,
        reset,
        headers: {
          'X-RateLimit-Limit': String(maxRequests),
          'X-RateLimit-Remaining': String(maxRequests),
          'X-RateLimit-Reset': String(reset),
        },
      }
    }
  }

  private getKvKey(tenantId: string, window: 'hour' | 'day', windowStart: number): string {
    const timestamp = Math.floor(windowStart / (window === 'hour' ? 3600000 : 86400000))
    return `rate:${tenantId}:${window}:${timestamp}`
  }
}
