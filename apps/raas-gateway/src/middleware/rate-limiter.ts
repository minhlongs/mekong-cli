/**
 * Rate Limiting Middleware — Applies token bucket rate limiting per tenant
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';
import { getTenant } from './auth';
import { RateLimitService } from '../services/rate-limit-service';
import { RateLimitError } from '../utils/errors';
import { json } from '../utils/response';

/**
 * Rate limiting middleware factory
 * Must be used AFTER auth middleware (requires tenant context)
 */
export function rateLimit(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const tenant = getTenant(c);
    const rateLimitService = new RateLimitService(c.env);

    const result = await rateLimitService.checkLimit(tenant.tenantId, tenant.tier);

    // Set rate limit headers on all responses
    c.header('X-RateLimit-Remaining', result.remaining.toString());
    c.header('X-RateLimit-Reset', result.resetAt.toString());

    if (!result.allowed) {
      // Set Retry-After header
      if (result.retryAfter) {
        c.header('Retry-After', result.retryAfter.toString());
      }

      // Return 429 Too Many Requests
      return json(
        {
          error: 'Rate limit exceeded',
          code: 'RATE_LIMIT_EXCEEDED',
          retryAfter: result.retryAfter,
          remaining: result.remaining,
        },
        { status: 429 }
      );
    }

    await next();
  };
}

/**
 * Get rate limit service from context
 */
export function getRateLimitService(c: { get: (key: string) => any }): RateLimitService {
  return c.get('rateLimitService');
}
