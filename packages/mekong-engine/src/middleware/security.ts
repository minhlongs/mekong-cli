/**
 * Security Headers Middleware
 * Protect against XSS, clickjacking, MIME sniffing, and other attacks
 *
 * Headers implemented:
 * - Content-Security-Policy (CSP)
 * - X-Frame-Options
 * - X-Content-Type-Options
 * - Strict-Transport-Security (HSTS)
 * - X-XSS-Protection
 * - Referrer-Policy
 * - Permissions-Policy
 * - X-Permitted-Cross-Domain-Policies
 * - Cross-Origin-Opener-Policy
 * - Cross-Origin-Embedder-Policy
 * - Cross-Origin-Resource-Policy
 */

import type { Context, Next } from 'hono'
import type { Bindings } from '../index'

export interface SecurityHeadersOptions {
  /**
   * Content Security Policy directives
   * Default: strict CSP for API
   */
  csp?: {
    /** Default src directive */
    defaultSrc?: string[]
    /** Script src directive */
    scriptSrc?: string[]
    /** Style src directive */
    styleSrc?: string[]
    /** Img src directive */
    imgSrc?: string[]
    /** Connect src directive */
    connectSrc?: string[]
    /** Font src directive */
    fontSrc?: string[]
    /** Object src directive */
    objectSrc?: string[]
    /** Frame ancestors directive */
    frameAncestors?: string[]
    /** Base uri directive */
    baseUri?: string[]
    /** Form action directive */
    formAction?: string[]
    /** Upgrade insecure requests */
    upgradeInsecureRequests?: boolean
  }

  /**
   * HSTS max-age in seconds
   * Default: 31536000 (1 year)
   */
  hstsMaxAge?: number

  /**
   * Include subdomains in HSTS
   * Default: true
   */
  hstsIncludeSubDomains?: boolean

  /**
   * HSTS preload
   * Default: true
   */
  hstsPreload?: boolean

  /**
   * Referrer Policy
   * Default: 'strict-origin-when-cross-origin'
   */
  referrerPolicy?: string

  /**
   * Permissions Policy
   * Default: restrictive for API
   */
  permissionsPolicy?: string[]

  /**
   * Skip headers for specific paths (e.g., webhooks)
   */
  skipPaths?: string[]
}

/**
 * Build CSP header value from directives
 */
function buildCspValue(options: Required<SecurityHeadersOptions>['csp']): string {
  const directives: string[] = []

  if (options.defaultSrc?.length) {
    directives.push(`default-src ${options.defaultSrc.join(' ')}`)
  }

  if (options.scriptSrc?.length) {
    directives.push(`script-src ${options.scriptSrc.join(' ')}`)
  }

  if (options.styleSrc?.length) {
    directives.push(`style-src ${options.styleSrc.join(' ')}`)
  }

  if (options.imgSrc?.length) {
    directives.push(`img-src ${options.imgSrc.join(' ')}`)
  }

  if (options.connectSrc?.length) {
    directives.push(`connect-src ${options.connectSrc.join(' ')}`)
  }

  if (options.fontSrc?.length) {
    directives.push(`font-src ${options.fontSrc.join(' ')}`)
  }

  if (options.objectSrc?.length) {
    directives.push(`object-src ${options.objectSrc.join(' ')}`)
  }

  if (options.frameAncestors?.length) {
    directives.push(`frame-ancestors ${options.frameAncestors.join(' ')}`)
  }

  if (options.baseUri?.length) {
    directives.push(`base-uri ${options.baseUri.join(' ')}`)
  }

  if (options.formAction?.length) {
    directives.push(`form-action ${options.formAction.join(' ')}`)
  }

  if (options.upgradeInsecureRequests) {
    directives.push('upgrade-insecure-requests')
  }

  return directives.join('; ')
}

/**
 * Default CSP for API-only endpoints
 * No inline scripts, no eval, restrictive origins
 */
const defaultApiCsp = {
  defaultSrc: ["'none'"],
  scriptSrc: ["'none'"],
  styleSrc: ["'none'"],
  imgSrc: ["'self'", 'data:', 'https:'],
  connectSrc: ["'self'"],
  fontSrc: ["'self'"],
  objectSrc: ["'none'"],
  frameAncestors: ["'none'"],
  baseUri: ["'none'"],
  formAction: ["'self'"],
  upgradeInsecureRequests: true,
}

/**
 * Default CSP for dashboard/frontend endpoints
 * Allows necessary resources for UI
 */
const defaultDashboardCsp = {
  defaultSrc: ["'self'"],
  scriptSrc: ["'self'", "'wasm-unsafe-eval'"],
  styleSrc: ["'self'", "'unsafe-inline'"],
  imgSrc: ["'self'", 'data:', 'https:', 'blob:'],
  connectSrc: ["'self'", 'https:'],
  fontSrc: ["'self'", 'https:'],
  objectSrc: ["'none'"],
  frameAncestors: ["'none'"],
  baseUri: ["'self'"],
  formAction: ["'self'"],
  upgradeInsecureRequests: true,
}

/**
 * Default permissions policy for API
 * Restrictive - disable most browser features
 */
const defaultPermissionsPolicy = [
  'accelerometer=()',
  'camera=()',
  'geolocation=()',
  'gyroscope=()',
  'magnetometer=()',
  'microphone=()',
  'payment=()',
  'usb=()',
  'fullscreen=()',
  'screen-wake-lock=()',
]

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
    // Skip headers for excluded paths (e.g., webhooks)
    if (skipPaths.some(path => c.req.path.includes(path))) {
      await next()
      return
    }

    await next()

    // Content-Security-Policy
    c.header('Content-Security-Policy', cspValue)

    // X-Frame-Options - prevent clickjacking
    c.header('X-Frame-Options', 'DENY')

    // X-Content-Type-Options - prevent MIME sniffing
    c.header('X-Content-Type-Options', 'nosniff')

    // Strict-Transport-Security - enforce HTTPS
    c.header('Strict-Transport-Security', hstsValue)

    // X-XSS-Protection - legacy XSS filter (for older browsers)
    c.header('X-XSS-Protection', '1; mode=block')

    // Referrer-Policy - control referrer information
    c.header('Referrer-Policy', referrerPolicy)

    // Permissions-Policy - disable unnecessary browser features
    c.header('Permissions-Policy', permissionsPolicyValue)

    // X-Permitted-Cross-Domain-Policies - Adobe Flash/PDF restrictions
    c.header('X-Permitted-Cross-Domain-Policies', 'none')

    // Cross-Origin-Opener-Policy - isolate browsing context
    c.header('Cross-Origin-Opener-Policy', 'same-origin')

    // Cross-Origin-Embedder-Policy - require CORS for cross-origin resources
    c.header('Cross-Origin-Embedder-Policy', 'require-corp')

    // Cross-Origin-Resource-Policy - restrict resource loading
    c.header('Cross-Origin-Resource-Policy', 'same-origin')

    // Cache-Control for sensitive API responses
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
 * (webhooks need to accept external requests)
 */
export function webhookSecurityHeaders() {
  return async (c: Context<{ Bindings: Bindings }>, next: Next) => {
    await next()

    // Only set essential headers for webhooks
    c.header('X-Content-Type-Options', 'nosniff')
    c.header('X-Frame-Options', 'DENY')
    c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
  }
}
