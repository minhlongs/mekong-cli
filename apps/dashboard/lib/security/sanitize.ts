/**
 * Input Sanitization & Validation
 * Protects against XSS, SQL injection, and malicious input
 */

import {
  detectSqlInjection,
  escapeHtml,
  isValidEmail,
  isValidRedirectUrl,
  sanitizeEmail,
  sanitizeSqlInput,
  sanitizeUrl,
  stripHtml,
} from './sanitize-html'

export interface SanitizeOptions {
  maxLength?: number
  stripHtml?: boolean
  allowNewlines?: boolean
  allowSpecialChars?: boolean
}

export function sanitizeInput(input: string, options: SanitizeOptions = {}): string {
  let result = input

  if (options.stripHtml) {
    result = stripHtml(result)
  }

  result = escapeHtml(result)
  result = result.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')

  if (!options.allowNewlines) {
    result = result.replace(/[\r\n]+/g, ' ')
  }

  if (!options.allowSpecialChars) {
    result = result.replace(/[<>{}[\]\\^`|~]/g, '')
  }

  result = result.trim()
  if (options.maxLength && result.length > options.maxLength) {
    result = result.substring(0, options.maxLength)
  }

  return result
}

export interface PasswordStrength {
  score: number // 0-100
  level: 'weak' | 'fair' | 'good' | 'strong'
  suggestions: string[]
}

export function checkPasswordStrength(password: string): PasswordStrength {
  const suggestions: string[] = []
  let score = 0

  if (password.length >= 8) score += 20
  else suggestions.push('Use at least 8 characters')

  if (password.length >= 12) score += 10
  if (password.length >= 16) score += 10

  if (/[a-z]/.test(password)) score += 10
  else suggestions.push('Add lowercase letters')

  if (/[A-Z]/.test(password)) score += 10
  else suggestions.push('Add uppercase letters')

  if (/[0-9]/.test(password)) score += 10
  else suggestions.push('Add numbers')

  if (/[^a-zA-Z0-9]/.test(password)) score += 15
  else suggestions.push('Add special characters')

  if (/^[a-z]+$|^[A-Z]+$|^[0-9]+$/.test(password)) {
    score -= 20
    suggestions.push('Avoid using only one type of character')
  }

  if (/(.)\1{2,}/.test(password)) {
    score -= 10
    suggestions.push('Avoid repeated characters')
  }

  const commonPasswords = ['password', '123456', 'qwerty', 'admin', 'letmein']
  if (commonPasswords.some(p => password.toLowerCase().includes(p))) {
    score -= 30
    suggestions.push('Avoid common passwords')
  }

  score = Math.max(0, Math.min(100, score))

  let level: PasswordStrength['level']
  if (score < 30) level = 'weak'
  else if (score < 50) level = 'fair'
  else if (score < 70) level = 'good'
  else level = 'strong'

  return { score, level, suggestions }
}

export function sanitizeObject<T extends Record<string, unknown>>(
  obj: T,
  fieldConfigs: Partial<Record<keyof T, SanitizeOptions>>
): T {
  const result = { ...obj }

  for (const [key, options] of Object.entries(fieldConfigs)) {
    const value = result[key as keyof T]
    if (typeof value === 'string' && options) {
      ;(result as Record<string, unknown>)[key] = sanitizeInput(value, options)
    }
  }

  return result
}

export interface ThreatDetectionResult {
  safe: boolean
  threats: string[]
}

export function detectThreats(input: string): ThreatDetectionResult {
  const threats: string[] = []

  if (/<script|javascript:|on\w+=/i.test(input)) {
    threats.push('Potential XSS attack')
  }

  if (detectSqlInjection(input)) {
    threats.push('Potential SQL injection')
  }

  if (/\.\.\/|\.\.\\/.test(input)) {
    threats.push('Path traversal attempt')
  }

  if (/[;&|`$]/.test(input)) {
    threats.push('Potential command injection')
  }

  if (/[()\\*]/.test(input) && /[=|&]/.test(input)) {
    threats.push('Potential LDAP injection')
  }

  return {
    safe: threats.length === 0,
    threats,
  }
}

export {
  detectSqlInjection,
  escapeHtml,
  isValidEmail,
  isValidRedirectUrl,
  sanitizeEmail,
  sanitizeSqlInput,
  sanitizeUrl,
  stripHtml,
}
