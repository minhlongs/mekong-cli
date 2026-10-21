/**
 * Security Headers Configuration
 * CSP, HSTS, and other security headers
 */

import type { NextResponse } from 'next/server'
import crypto from 'crypto'
import {
  buildCSP,
  buildPermissionsPolicy,
  CSP_DIRECTIVES,
  defaultConfig,
  PERMISSIONS_POLICY,
  type SecurityHeadersConfig,
  securityHeadersConfig,
} from './headers-config'

export function applySecurityHeaders(
  response: NextResponse,
  config: Partial<SecurityHeadersConfig> = {},
  nonce?: string
): NextResponse {
  const finalConfig = { ...defaultConfig, ...config }

  if (finalConfig.enableCSP) {
    response.headers.set(
      'Content-Security-Policy',
      buildCSP(finalConfig.customCSPDirectives, nonce)
    )
  }

  if (finalConfig.enableHSTS) {
    response.headers.set(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains; preload'
    )
  }

  if (finalConfig.enableFrameOptions) {
    response.headers.set('X-Frame-Options', 'SAMEORIGIN')
  }

  if (finalConfig.enableXSSProtection) {
    response.headers.set('X-XSS-Protection', '1; mode=block')
  }

  if (finalConfig.enableContentTypeOptions) {
    response.headers.set('X-Content-Type-Options', 'nosniff')
  }

  if (finalConfig.enableReferrerPolicy) {
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  }

  if (finalConfig.enablePermissionsPolicy) {
    response.headers.set('Permissions-Policy', buildPermissionsPolicy())
  }

  response.headers.set('X-DNS-Prefetch-Control', 'on')
  response.headers.set('X-Download-Options', 'noopen')
  response.headers.set('X-Permitted-Cross-Domain-Policies', 'none')

  return response
}

export function generateNonce(): string {
  return crypto.randomBytes(16).toString('base64')
}

export function getCSPHeaders(nonce?: string): Array<{ key: string; value: string }> {
  const baseHeaders = securityHeadersConfig.filter(h => h.key !== 'Content-Security-Policy')

  const cspHeader = {
    key: 'Content-Security-Policy',
    value: buildCSP(undefined, nonce),
  }

  return [...baseHeaders, cspHeader]
}

export function getSecurityHeaders() {
  return [
    {
      source: '/:path*',
      headers: securityHeadersConfig,
    },
  ]
}

export {
  buildCSP,
  buildPermissionsPolicy,
  CSP_DIRECTIVES,
  PERMISSIONS_POLICY,
  type SecurityHeadersConfig,
  securityHeadersConfig,
}
