/**
 * Rate Limiting Middleware - Token Bucket Algorithm
 * Uses Cloudflare KV for distributed rate limiting across edge locations
 */

import { createMiddleware } from 'hono/factory'
import type { Context, Next } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import type { KVNamespace } from '@cloudflare/workers-types'
import { getRateLimitConfig, type TenantTier, getRetryAfterSeconds } from '../lib/tenant-limits'
import { logger } from '../lib/monitoring'
import { createError } from '../types/error'

/**
 * Rate limit state stored in KV
 */
interface RateLimitState {
  count: number
  windowStart: number
}

/**
 * Rate limit response headers
 */
interface RateLimitHeaders extends Record<string, string> {
  'X-RateLimit-Limit': string
  'X-RateLimit-Remaining': string
  'X-RateLimit-Reset': string
}

/**
 * Rate limit exceeded response body
 */
interface RateLimitExceededResponse {
  error: string
  code: string
  retry_after: number
  limit: number
  remaining: number
  reset: number
}

/**
 * Token Bucket Rate Limiter using Cloudflare KV
 */
class TokenBucketLimiter {
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
      // Get current count from KV
      const stored = await this.kv.get(kvKey, 'json') as RateLimitState | null
      let state: RateLimitState

      // Reset counter if window has passed
      if (!stored || stored.windowStart < windowStart) {
        state = { count: 0, windowStart }
      } else {
        state = stored
      }

      // Check if limit exceeded
      const remaining = Math.max(0, maxRequests - state.count)
      const reset = Math.ceil(windowEnd / 1000) // Unix timestamp in seconds

      if (state.count >= maxRequests) {
        // Rate limit exceeded
        const headers: RateLimitHeaders = {
          'X-RateLimit-Limit': String(maxRequests),
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(reset),
          'Retry-After': String(Math.ceil((windowEnd - now) / 1000)),
        }

        return {
          allowed: false,
          limit: maxRequests,
          remaining: 0,
          reset,
          headers,
        }
      }

      // Increment counter
      state.count++
      await this.kv.put(kvKey, JSON.stringify(state), {
        expirationTtl: Math.ceil(windowMs / 1000) + 60, // TTL = window + 1 min buffer
      })

      const headers: RateLimitHeaders = {
        'X-RateLimit-Limit': String(maxRequests),
        'X-RateLimit-Remaining': String(remaining - 1),
        'X-RateLimit-Reset': String(reset),
      }

      return {
        allowed: true,
        limit: maxRequests,
        remaining: remaining - 1,
        reset,
        headers,
      }
    } catch (error) {
      // If KV fails, log error but allow request (fail-open for availability)
      logger.error('Rate limit KV operation failed', {
        error: error instanceof Error ? error.message : String(error),
        tenantId,
        window,
      })

      const reset = Math.ceil((windowEnd - now) / 1000)
      const headers: RateLimitHeaders = {
        'X-RateLimit-Limit': String(maxRequests),
        'X-RateLimit-Remaining': String(maxRequests),
        'X-RateLimit-Reset': String(reset),
      }

      return {
        allowed: true,
        limit: maxRequests,
        remaining: maxRequests,
        reset,
        headers,
      }
    }
  }

  /**
   * Generate KV key for rate limit storage
   */
  private getKvKey(tenantId: string, window: 'hour' | 'day', windowStart: number): string {
    const timestamp = Math.floor(windowStart / (window === 'hour' ? 3600000 : 86400000))
    return `rate:${tenantId}:${window}:${timestamp}`
  }
}

/**
 * Create rate limiting middleware
 * Checks both hourly and daily limits before allowing request
 */
export function rateLimitMiddleware() {
  return createMiddleware<{ Bindings: Bindings; Variables: { tenant: Tenant } }>(
    async (c: Context<{ Bindings: Bindings; Variables: { tenant: Tenant } }>, next: Next) => {
      // Skip rate limiting if KV not available (development mode)
      if (!c.env.RATE_LIMIT_KV) {
        logger.warn('Rate limiting disabled - RATE_LIMIT_KV binding not configured')
        await next()
        return
      }

      // Get tenant from context (set by auth middleware)
      const tenant = c.get('tenant')
      if (!tenant) {
        // No tenant = anonymous request, skip rate limiting
        // (auth middleware handles unauthorized requests)
        await next()
        return
      }

      const limiter = new TokenBucketLimiter(c.env.RATE_LIMIT_KV)
      const tier = (tenant.tier as TenantTier) || 'free'
      const tenantId = tenant.id

      // Check hourly limit first (more restrictive short-term)
      const hourlyResult = await limiter.check(tenantId, tier, 'hour')
      if (!hourlyResult.allowed) {
        const response: RateLimitExceededResponse = {
          error: 'Rate limit exceeded',
          code: 'RATE_LIMIT_EXCEEDED',
          retry_after: getRetryAfterSeconds('hour'),
          limit: hourlyResult.limit,
          remaining: hourlyResult.remaining,
          reset: hourlyResult.reset,
        }

        logger.warn('Hourly rate limit exceeded', {
          tenantId,
          tier,
          limit: hourlyResult.limit,
        })

        return c.json(response, 429, hourlyResult.headers)
      }

      // Check daily limit
      const dailyResult = await limiter.check(tenantId, tier, 'day')
      if (!dailyResult.allowed) {
        const response: RateLimitExceededResponse = {
          error: 'Rate limit exceeded',
          code: 'RATE_LIMIT_EXCEEDED',
          retry_after: getRetryAfterSeconds('day'),
          limit: dailyResult.limit,
          remaining: dailyResult.remaining,
          reset: dailyResult.reset,
        }

        logger.warn('Daily rate limit exceeded', {
          tenantId,
          tier,
          limit: dailyResult.limit,
        })

        return c.json(response, 429, dailyResult.headers)
      }

      // Set rate limit headers on response
      c.header('X-RateLimit-Limit', String(dailyResult.limit))
      c.header('X-RateLimit-Remaining', String(dailyResult.remaining))
      c.header('X-RateLimit-Reset', String(dailyResult.reset))

      await next()
    }
  )
}

/**
 * Export as default for easy import
 */
export default rateLimitMiddleware
