/**
 * Request ID middleware — traces requests via X-Request-Id header
 * Generates UUID if client doesn't provide one, measures response time
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';

// Extend Hono context with requestId
declare module 'hono' {
  interface ContextVariableMap {
    requestId: string;
  }
}

/**
 * Middleware: attach X-Request-Id and X-Response-Time headers
 * - Accepts client-provided X-Request-Id or generates a UUID
 * - Stores in context variable for downstream use
 */
export function requestId(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const start = Date.now();

    // Prefer client-provided ID, fall back to generated UUID
    const id = c.req.header('X-Request-Id') ?? crypto.randomUUID();
    c.set('requestId', id);

    await next();

    // Attach tracing headers to response
    c.header('X-Request-Id', id);
    c.header('X-Response-Time', `${Date.now() - start}ms`);
  };
}
