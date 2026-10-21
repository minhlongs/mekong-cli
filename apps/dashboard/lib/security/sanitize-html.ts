/**
 * HTML, SQL, URL, and Email Sanitization Utilities
 */

const HTML_ENTITIES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#x27;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;',
}

export function escapeHtml(input: string): string {
  return input.replace(/[&<>"'`=/]/g, char => HTML_ENTITIES[char] || char)
}

export function stripHtml(input: string): string {
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
    .replace(/<[^>]+>/g, '')
    .trim()
}

const SQL_INJECTION_PATTERNS = [
  /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|UNION|DECLARE)\b)/gi,
  /(-{2}|;|\*|\/\*|\*\/)/g,
  /(\bOR\b|\bAND\b)[\s]*[\d\w'"][\s]*(=|LIKE)/gi,
  /('|\"|;|--)/g,
]

export function detectSqlInjection(input: string): boolean {
  for (const pattern of SQL_INJECTION_PATTERNS) {
    if (pattern.test(input)) {
      return true
    }
    pattern.lastIndex = 0
  }
  return false
}

export function sanitizeSqlInput(input: string): string {
  return input
    .replace(/['";\\]/g, '')
    .replace(/--/g, '')
    .trim()
}

export function sanitizeUrl(url: string): string | null {
  try {
    const parsed = new URL(url)

    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return null
    }

    if (url.toLowerCase().includes('javascript:')) {
      return null
    }

    if (url.toLowerCase().startsWith('data:')) {
      return null
    }

    return parsed.toString()
  } catch {
    return null
  }
}

export function isValidRedirectUrl(url: string, allowedDomains: string[]): boolean {
  try {
    const parsed = new URL(url)
    return allowedDomains.some(
      domain => parsed.hostname === domain || parsed.hostname.endsWith(`.${domain}`)
    )
  } catch {
    return url.startsWith('/') && !url.startsWith('//')
  }
}

export function sanitizeEmail(email: string): string {
  return email
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9@._+-]/g, '')
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return emailRegex.test(email) && email.length <= 254
}
