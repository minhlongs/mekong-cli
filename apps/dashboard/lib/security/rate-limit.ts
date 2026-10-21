/**
 * Redis-backed Rate Limiting Middleware
 * Persistent rate limiting for production environments
 */

import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import {
  getRedisClient,
  RATE_LIMITS,
  type RateLimitConfig,
  type RateLimitResult,
  RedisRateLimiter,
} from './rate-limit-store'

export const rateLimiter = new RedisRateLimiter()

export async function rateLimitMiddleware(
  request: NextRequest,
  limitType: string = 'api:default'
): Promise<NextResponse | null> {
  const ip =
    request.headers.get('x-forwarded-for')?.split(',')[0] ||
    request.headers.get('x-real-ip') ||
    'unknown'

  const userId = request.headers.get('x-user-id')
  const identifier = userId || ip

  const result = await rateLimiter.check(identifier, limitType)

  if (!result.allowed) {
    return NextResponse.json(
      {
        error: 'Rate limit exceeded',
        retryAfter: Math.ceil((result.resetAt.getTime() - Date.now()) / 1000),
        blockedUntil: result.blockedUntil?.toISOString(),
      },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': String(RATE_LIMITS[limitType]?.maxRequests || 100),
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': result.resetAt.toISOString(),
          'Retry-After': String(Math.ceil((result.resetAt.getTime() - Date.now()) / 1000)),
        },
      }
    )
  }

  return null
}

export function addRateLimitHeaders(
  response: NextResponse,
  result: RateLimitResult,
  limitType: string
): NextResponse {
  const config = RATE_LIMITS[limitType] || RATE_LIMITS['api:default']

  response.headers.set('X-RateLimit-Limit', String(config.maxRequests))
  response.headers.set('X-RateLimit-Remaining', String(result.remaining))
  response.headers.set('X-RateLimit-Reset', result.resetAt.toISOString())

  return response
}

export {
  getRedisClient,
  RATE_LIMITS,
  type RateLimitConfig,
  type RateLimitResult,
  RedisRateLimiter,
}
