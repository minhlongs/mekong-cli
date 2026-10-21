/**
 * CSP Directives & Default Security Header Configurations
 */

export interface SecurityHeadersOptions {
  /** Content Security Policy directives (Default: strict CSP for API) */
  csp?: {
    defaultSrc?: string[]
    scriptSrc?: string[]
    styleSrc?: string[]
    imgSrc?: string[]
    connectSrc?: string[]
    fontSrc?: string[]
    objectSrc?: string[]
    frameAncestors?: string[]
    baseUri?: string[]
    formAction?: string[]
    upgradeInsecureRequests?: boolean
  }
  /** HSTS max-age in seconds (Default: 31536000) */
  hstsMaxAge?: number
  /** Include subdomains in HSTS (Default: true) */
  hstsIncludeSubDomains?: boolean
  /** HSTS preload (Default: true) */
  hstsPreload?: boolean
  /** Referrer Policy (Default: 'strict-origin-when-cross-origin') */
  referrerPolicy?: string
  /** Permissions Policy (Default: restrictive for API) */
  permissionsPolicy?: string[]
  /** Skip headers for specific paths (e.g., webhooks) */
  skipPaths?: string[]
}

/**
 * Build CSP header value from directives
 */
export function buildCspValue(options: NonNullable<SecurityHeadersOptions['csp']>): string {
  const directives: string[] = []

  if (options.defaultSrc?.length) directives.push(`default-src ${options.defaultSrc.join(' ')}`)
  if (options.scriptSrc?.length) directives.push(`script-src ${options.scriptSrc.join(' ')}`)
  if (options.styleSrc?.length) directives.push(`style-src ${options.styleSrc.join(' ')}`)
  if (options.imgSrc?.length) directives.push(`img-src ${options.imgSrc.join(' ')}`)
  if (options.connectSrc?.length) directives.push(`connect-src ${options.connectSrc.join(' ')}`)
  if (options.fontSrc?.length) directives.push(`font-src ${options.fontSrc.join(' ')}`)
  if (options.objectSrc?.length) directives.push(`object-src ${options.objectSrc.join(' ')}`)
  if (options.frameAncestors?.length) directives.push(`frame-ancestors ${options.frameAncestors.join(' ')}`)
  if (options.baseUri?.length) directives.push(`base-uri ${options.baseUri.join(' ')}`)
  if (options.formAction?.length) directives.push(`form-action ${options.formAction.join(' ')}`)
  if (options.upgradeInsecureRequests) directives.push('upgrade-insecure-requests')

  return directives.join('; ')
}

export const defaultApiCsp = {
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

export const defaultDashboardCsp = {
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

export const defaultPermissionsPolicy = [
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
