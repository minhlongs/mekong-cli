/**
 * Security headers middleware for Cloudflare Workers
 * Hardens HTTP responses against common web vulnerabilities
 */

import type { MiddlewareHandler } from 'hono';

export function securityHeaders(): MiddlewareHandler {
  return async (c, next) => {
    await next();

    // HSTS — force HTTPS for 1 year including subdomains
    c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');

    // Prevent clickjacking via iframe embedding
    c.header('X-Frame-Options', 'DENY');

    // Prevent MIME type sniffing
    c.header('X-Content-Type-Options', 'nosniff');

    // Legacy XSS filter (IE/older browsers)
    c.header('X-XSS-Protection', '1; mode=block');

    // Limit referrer information in cross-origin requests
    c.header('Referrer-Policy', 'strict-origin-when-cross-origin');

    // Restrict browser feature access
    c.header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

    // CSP — allow self and HTTPS API calls only
    c.header(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https:; img-src 'self' data: https:"
    );
  };
}
