/**
 * Rate Limiting Middleware - Token Bucket Algorithm
 * Uses Cloudflare KV for distributed rate limiting across edge locations
 */

import { createMiddleware } from 'hono/factory'
import type { Context, Next } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { type TenantTier, getRetryAfterSeconds } from '../lib/tenant-limits'
import { logger } from '../lib/monitoring'
import {
  TokenBucketLimiter,
  type RateLimitExceededResponse,
} from './token-bucket-limiter'

/**
 * Create rate limiting middleware
 * Checks both hourly and daily limits before allowing request
 */
export function rateLimitMiddleware() {
  return createMiddleware<{ Bindings: Bindings; Variables: { tenant: Tenant } }>(
    async (c: Context<{ Bindings: Bindings; Variables: { tenant: Tenant } }>, next: Next) => {
      if (!c.env.RATE_LIMIT_KV) {
        logger.warn('Rate limiting disabled - RATE_LIMIT_KV binding not configured')
        await next()
        return
      }

      const tenant = c.get('tenant')
      if (!tenant) {
        await next()
        return
      }

      const limiter = new TokenBucketLimiter(c.env.RATE_LIMIT_KV)
      const tier = (tenant.tier as TenantTier) || 'free'
      const tenantId = tenant.id

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

      c.header('X-RateLimit-Limit', String(dailyResult.limit))
      c.header('X-RateLimit-Remaining', String(dailyResult.remaining))
      c.header('X-RateLimit-Reset', String(dailyResult.reset))

      await next()
    }
  )
}

export default rateLimitMiddleware
