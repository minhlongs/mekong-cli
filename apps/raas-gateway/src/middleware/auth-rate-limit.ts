/**
 * Rate limiting middleware for webhook endpoints
 * Stricter rate limits for external webhooks
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';

// Webhook rate limits (per minute)
const WEBHOOK_LIMITS = {
  maxRequests: 100,      // Max requests per minute
  windowMs: 60 * 1000,   // 1 minute window
};

export function authRateLimit(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const clientIp = c.req.header('x-forwarded-for') || c.req.header('x-real-ip') || 'unknown';
    const key = `ratelimit:webhook:${clientIp}`;
    const now = Date.now();

    try {
      // Get current window state
      const data = await c.env.RATE_LIMIT_KV.get(key, 'json') as {
        count: number;
        windowStart: number;
      } | null;

      let count = 0;
      let windowStart = now;

      if (data) {
        const elapsed = now - data.windowStart;

        if (elapsed < WEBHOOK_LIMITS.windowMs) {
          // Same window
          count = data.count;
          windowStart = data.windowStart;
        }
      }

      // Increment counter
      count++;

      // Check limit
      if (count > WEBHOOK_LIMITS.maxRequests) {
        c.header('Retry-After', Math.ceil((windowStart + WEBHOOK_LIMITS.windowMs - now) / 1000).toString());
        c.header('X-RateLimit-Limit', WEBHOOK_LIMITS.maxRequests.toString());
        c.header('X-RateLimit-Remaining', '0');

        return c.json(
          {
            error: 'Rate limit exceeded',
            code: 'WEBHOOK_RATE_LIMIT_EXCEEDED',
            retryAfter: Math.ceil((windowStart + WEBHOOK_LIMITS.windowMs - now) / 1000),
          },
          { status: 429 }
        );
      }

      // Store updated state
      await c.env.RATE_LIMIT_KV.put(
        key,
        JSON.stringify({ count, windowStart }),
        { expirationTtl: 120 }
      );

      // Set headers
      c.header('X-RateLimit-Limit', WEBHOOK_LIMITS.maxRequests.toString());
      c.header('X-RateLimit-Remaining', (WEBHOOK_LIMITS.maxRequests - count).toString());

      await next();
    } catch (error) {
      console.error('[RateLimit] Webhook rate limit error:', error);
      // Fail closed — reject if KV unavailable (prevents abuse during outage)
      return c.json(
        { error: 'Rate limiting unavailable', code: 'SERVICE_UNAVAILABLE' },
        { status: 503 }
      );
    }
  };
}
