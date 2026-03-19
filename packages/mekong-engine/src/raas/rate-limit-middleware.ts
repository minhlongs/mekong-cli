import type { Context } from 'hono'
import type { KVNamespace } from '@cloudflare/workers-types'
import { createError } from '../types/error'
import { checkStrictRateLimit, recordStrictRateLimit } from './rate-limiter'

/**
 * Middleware: Strict rate limiting for sensitive endpoints
 * Use for webhooks, payment endpoints, auth endpoints
 *
 * @param maxRequests Max requests per window (default: 10)
 * @param windowMs Window size in ms (default: 60000 = 1 minute)
 */
export function rateLimitMiddleware(
  endpointName: string,
  maxRequests: number = 10,
  windowMs: number = 60000,
) {
  return async (c: Context, next: () => Promise<void>) => {
    const kv = c.env.RATE_LIMIT_KV
    if (!kv) {
      // KV not available - skip rate limiting gracefully (dev environment)
      await next()
      return
    }

    // Create unique endpoint key
    const endpoint = `${endpointName}:${c.req.path}`

    const result = await checkStrictRateLimit(kv, endpoint, maxRequests, windowMs)

    if (!result.allowed) {
      c.res = c.json(
        {
          error: 'RATE_LIMIT_EXCEEDED',
          message: `Too many requests. Maximum ${maxRequests} requests per ${windowMs / 1000} seconds.`,
          retry_after: result.retryAfter,
        },
        429,
      )
      c.res.headers.set('Retry-After', String(result.retryAfter))
      return
    }

    // Record this request after successful processing
    await next()
    await recordStrictRateLimit(kv, endpoint, windowMs)
  }
}

/**
 * Preset: Webhook rate limiting (strict - 10 req/min)
 * Use for Polar, MoMo, VNPAY, Zalo, Facebook webhooks
 */
export const webhookRateLimit = () => rateLimitMiddleware('webhook', 10, 60000)

/**
 * Preset: Payment endpoint rate limiting (50 req/min)
 * Use for payment creation, checkout endpoints
 */
export const paymentRateLimit = () => rateLimitMiddleware('payment', 50, 60000)

/**
 * Preset: Auth endpoint rate limiting (20 req/min)
 * Use for login, token refresh endpoints
 */
export const authRateLimit = () => rateLimitMiddleware('auth', 20, 60000)
