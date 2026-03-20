/**
 * Request logging middleware with correlation IDs
 */

import type { MiddlewareHandler, Context } from 'hono';

export function logger(): MiddlewareHandler {
  return async (c, next) => {
    const startTime = Date.now();
    const correlationId = c.req.header('X-Correlation-ID') || crypto.randomUUID();

    // Add correlation ID to response headers
    c.header('X-Correlation-ID', correlationId);
    c.set('correlationId', correlationId);

    const method = c.req.method;
    const path = c.req.path;

    console.log(`[${correlationId}] --> ${method} ${path}`);

    await next();

    const duration = Date.now() - startTime;
    const status = c.res.status;

    console.log(`[${correlationId}] <-- ${status} ${method} ${path} (${duration}ms)`);
  };
}

// Helper to get correlation ID from context
export function getCorrelationId(c: Context): string {
  return c.get('correlationId') || 'unknown';
}
