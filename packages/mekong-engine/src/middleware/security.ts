/**
 * Security Headers Middleware
 * Protect against XSS, clickjacking, MIME sniffing, and other attacks
 */

import type { Context, Next } from 'hono'
import type { Bindings } from '../index'
import {
  type SecurityHeadersOptions,
  buildCspValue,
  defaultApiCsp,
  defaultDashboardCsp,
  defaultPermissionsPolicy,
} from './security-csp-config'

export type { SecurityHeadersOptions }

/**
 * Security headers middleware factory
 */
export function securityHeaders(options: SecurityHeadersOptions = {}) {
  const {
    csp = defaultApiCsp,
    hstsMaxAge = 31536000,
    hstsIncludeSubDomains = true,
    hstsPreload = true,
    referrerPolicy = 'strict-origin-when-cross-origin',
    permissionsPolicy = defaultPermissionsPolicy,
    skipPaths = [],
  } = options

  const cspValue = buildCspValue(csp)
  const hstsValue = `max-age=${hstsMaxAge}${hstsIncludeSubDomains ? '; includeSubDomains' : ''}${hstsPreload ? '; preload' : ''}`
  const permissionsPolicyValue = permissionsPolicy.join(', ')

  return async (c: Context<{ Bindings: Bindings }>, next: Next) => {
    if (skipPaths.some(path => c.req.path.includes(path))) {
      await next()
      return
    }

    await next()

    c.header('Content-Security-Policy', cspValue)
    c.header('X-Frame-Options', 'DENY')
    c.header('X-Content-Type-Options', 'nosniff')
    c.header('Strict-Transport-Security', hstsValue)
    c.header('X-XSS-Protection', '1; mode=block')
    c.header('Referrer-Policy', referrerPolicy)
    c.header('Permissions-Policy', permissionsPolicyValue)
    c.header('X-Permitted-Cross-Domain-Policies', 'none')
    c.header('Cross-Origin-Opener-Policy', 'same-origin')
    c.header('Cross-Origin-Embedder-Policy', 'require-corp')
    c.header('Cross-Origin-Resource-Policy', 'same-origin')

    if (c.req.path.startsWith('/v1/') || c.req.path.startsWith('/billing')) {
      c.header('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate')
      c.header('Pragma', 'no-cache')
      c.header('Expires', '0')
    }
  }
}

/**
 * Security headers preset for API endpoints
 */
export const apiSecurityHeaders = securityHeaders({
  csp: defaultApiCsp,
  skipPaths: ['/webhooks'],
})

/**
 * Security headers preset for dashboard endpoints
 */
export const dashboardSecurityHeaders = securityHeaders({
  csp: defaultDashboardCsp,
  skipPaths: ['/webhooks'],
})

/**
 * Minimal security headers for webhook endpoints
 */
export function webhookSecurityHeaders() {
  return async (c: Context<{ Bindings: Bindings }>, next: Next) => {
    await next()
    c.header('X-Content-Type-Options', 'nosniff')
    c.header('X-Frame-Options', 'DENY')
    c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
  }
}
