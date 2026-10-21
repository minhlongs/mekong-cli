/**
 * Security Headers Policies & Builders (CSP, Permissions Policy)
 */

export interface SecurityHeadersConfig {
  enableCSP: boolean
  enableHSTS: boolean
  enableFrameOptions: boolean
  enableXSSProtection: boolean
  enableContentTypeOptions: boolean
  enableReferrerPolicy: boolean
  enablePermissionsPolicy: boolean
  customCSPDirectives?: Record<string, string[]>
}

export const defaultConfig: SecurityHeadersConfig = {
  enableCSP: true,
  enableHSTS: true,
  enableFrameOptions: true,
  enableXSSProtection: true,
  enableContentTypeOptions: true,
  enableReferrerPolicy: true,
  enablePermissionsPolicy: true,
}

export const CSP_DIRECTIVES: Record<string, string[]> = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    'https://js.stripe.com',
    'https://www.googletagmanager.com',
    'https://www.google-analytics.com',
  ],
  'style-src': ["'self'", 'https://fonts.googleapis.com'],
  'img-src': ["'self'", 'data:', 'blob:', 'https:'],
  'font-src': ["'self'", 'https://fonts.gstatic.com'],
  'connect-src': [
    "'self'",
    'https://api.stripe.com',
    'https://www.google-analytics.com',
    'wss://*.supabase.co',
    'https://*.supabase.co',
  ],
  'frame-src': ["'self'", 'https://js.stripe.com', 'https://hooks.stripe.com'],
  'object-src': ["'none'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"],
  'frame-ancestors': ["'self'"],
  'upgrade-insecure-requests': [],
}

export function buildCSP(customDirectives?: Record<string, string[]>, nonce?: string): string {
  const directives: Record<string, string[]> = {}
  for (const [key, values] of Object.entries({ ...CSP_DIRECTIVES, ...customDirectives })) {
    directives[key] = [...values]
  }

  if (nonce) {
    if (directives['script-src']) {
      directives['script-src'].push(`'nonce-${nonce}'`)
    }
    if (directives['style-src']) {
      directives['style-src'].push(`'nonce-${nonce}'`)
    }
  }

  return Object.entries(directives)
    .map(([key, values]) => {
      if (values.length === 0) return key
      return `${key} ${values.join(' ')}`
    })
    .join('; ')
}

export const PERMISSIONS_POLICY: Record<string, string[]> = {
  camera: [],
  microphone: [],
  geolocation: [],
  'interest-cohort': [],
  payment: ['self', 'https://js.stripe.com'],
  fullscreen: ['self'],
  autoplay: ['self'],
}

export function buildPermissionsPolicy(): string {
  return Object.entries(PERMISSIONS_POLICY)
    .map(([feature, origins]) => {
      if (origins.length === 0) return `${feature}=()`
      return `${feature}=(${origins.join(' ')})`
    })
    .join(', ')
}

export const securityHeadersConfig = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: buildPermissionsPolicy() },
]
