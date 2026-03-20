/**
 * CORS middleware for Cloudflare Workers
 */

import type { MiddlewareHandler } from 'hono';

interface CorsOptions {
  origin?: string | string[];
  allowMethods?: string[];
  allowHeaders?: string[];
  maxAge?: number;
  credentials?: boolean;
}

const defaultOptions: CorsOptions = {
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-Tenant-ID', 'X-Correlation-ID'],
  maxAge: 86400,
  credentials: false,
};

export function cors(options: CorsOptions = {}): MiddlewareHandler {
  const opts = { ...defaultOptions, ...options };

  return async (c, next) => {
    const origin = Array.isArray(opts.origin)
      ? opts.origin[0]
      : opts.origin || '*';

    c.header('Access-Control-Allow-Origin', origin);
    c.header('Access-Control-Allow-Methods', opts.allowMethods!.join(', '));
    c.header('Access-Control-Allow-Headers', opts.allowHeaders!.join(', '));
    c.header('Access-Control-Max-Age', String(opts.maxAge!));

    if (opts.credentials) {
      c.header('Access-Control-Allow-Credentials', 'true');
    }

    // Handle preflight
    if (c.req.method === 'OPTIONS') {
      return c.body(null, 204);
    }

    await next();
  };
}
