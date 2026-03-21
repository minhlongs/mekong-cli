/**
 * Request logging middleware — correlation IDs and response time tracking
 */

import type { MiddlewareHandler, Context } from 'hono';

export function logger(): MiddlewareHandler {
  return async (c, next) => {
    const startTime = Date.now();
    const correlationId = c.req.header('X-Correlation-ID') || crypto.randomUUID();

    // Add correlation ID to response headers and context
    c.header('X-Correlation-ID', correlationId);
    c.set('correlationId', correlationId);

    const method = c.req.method;
    const path = c.req.path;

    console.log(`[${correlationId}] --> ${method} ${path}`);

    await next();

    const duration = Date.now() - startTime;
    const status = c.res.status;

    // Attach response time header so clients can measure latency
    c.header('X-Response-Time', `${duration}ms`);

    console.log(`[${correlationId}] <-- ${status} ${method} ${path} (${duration}ms)`);
  };
}

// Helper to get correlation ID from context
export function getCorrelationId(c: Context): string {
  return c.get('correlationId') || 'unknown';
}
