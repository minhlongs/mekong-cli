/**
 * Shared utilities for route handlers
 *
 * Provides common helpers for tenant validation, input sanitization,
 * and edge case handling across all API endpoints.
 */

import type { D1Database } from '@cloudflare/workers-types'
import { HttpError } from '../types/error'

/**
 * Validate tenant exists in database
 * Throws NOT_FOUND error if tenant doesn't exist
 *
 * @param db - D1 database instance
 * @param tenantId - Tenant ID to validate
 * @throws HttpError with NOT_FOUND code
 */
export async function validateTenantExists(
  db: D1Database,
  tenantId: string
): Promise<void> {
  const tenant = await db
    .prepare('SELECT id FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first()

  if (!tenant) {
    throw new HttpError('NOT_FOUND', 'Tenant not found or has been deleted', undefined, 404)
  }
}

/**
 * Sanitize string input - trim whitespace and limit length
 *
 * @param value - Input string
 * @param maxLength - Maximum allowed length (default: 1000)
 * @returns Sanitized string
 */
export function sanitizeString(value: string, maxLength: number = 1000): string {
  const trimmed = value.trim()
  if (trimmed.length > maxLength) {
    return trimmed.slice(0, maxLength)
  }
  return trimmed
}

/**
 * Parse and validate pagination parameters
 * Returns safe, bounded values
 *
 * @param limit - Requested limit
 * @param offset - Requested offset
 * @param defaultLimit - Default limit (default: 50)
 * @param maxLimit - Maximum allowed limit (default: 200)
 * @returns Bounded { limit, offset }
 */
export function parsePagination(
  limit: unknown,
  offset: unknown,
  defaultLimit: number = 50,
  maxLimit: number = 200
): { limit: number; offset: number } {
  const parsedLimit =
    typeof limit === 'string'
      ? parseInt(limit, 10)
      : typeof limit === 'number'
      ? limit
      : defaultLimit

  const parsedOffset =
    typeof offset === 'string'
      ? parseInt(offset, 10)
      : typeof offset === 'number'
      ? offset
      : 0

  const safeLimit = isNaN(parsedLimit) ? defaultLimit : Math.max(1, Math.min(maxLimit, parsedLimit))
  const safeOffset = isNaN(parsedOffset) ? 0 : Math.max(0, parsedOffset)

  return { limit: safeLimit, offset: safeOffset }
}

/**
 * Safe date parsing with fallback
 * Returns ISO string or null if invalid
 *
 * @param value - Date string or timestamp
 * @returns ISO date string or null
 */
export function safeDate(value: unknown): string | null {
  if (!value) return null

  const date =
    typeof value === 'string'
      ? new Date(value)
      : typeof value === 'number'
      ? new Date(value)
      : null

  if (!date || isNaN(date.getTime())) return null

  return date.toISOString()
}

/**
 * Validate UUID format (basic check)
 *
 * @param value - UUID string to validate
 * @returns True if valid UUID v4 format
 */
export function isValidUuid(value: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(value)
}

/**
 * Require non-empty string
 * Throws BAD_REQUEST if value is empty or whitespace
 *
 * @param value - String to validate
 * @param fieldName - Field name for error message
 * @returns Trimmed string
 * @throws HttpError with BAD_REQUEST code
 */
export function requireNonEmptyString(value: string, fieldName: string): string {
  const trimmed = value?.trim() ?? ''
  if (trimmed.length === 0) {
    throw new HttpError('BAD_REQUEST', `${fieldName} is required`, undefined, 400)
  }
  return trimmed
}

/**
 * Safe array access with bounds checking
 * Returns fallback if index out of bounds
 *
 * @param arr - Array to access
 * @param index - Index to access
 * @param fallback - Fallback value
 * @returns Array element or fallback
 */
export function safeArrayAccess<T>(arr: T[], index: number, fallback: T): T {
  if (!Array.isArray(arr)) return fallback
  if (index < 0 || index >= arr.length) return fallback
  return arr[index]
}

/**
 * Clamp number between min and max
 *
 * @param value - Number to clamp
 * @param min - Minimum value
 * @param max - Maximum value
 * @returns Clamped number
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

/**
 * Parse JSON safely with fallback
 * Returns fallback on parse error
 *
 * @param jsonString - JSON string to parse
 * @param fallback - Fallback value on error
 * @returns Parsed object or fallback
 */
export function safeJsonParse<T>(jsonString: string | null | undefined, fallback: T): T {
  if (!jsonString) return fallback
  try {
    return JSON.parse(jsonString) as T
  } catch {
    return fallback
  }
}

/**
 * Validate email format (basic regex check)
 *
 * @param email - Email to validate
 * @returns True if valid email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Get boolean from various input types
 * Handles string, number, boolean inputs
 *
 * @param value - Input value
 * @param defaultValue - Default if cannot parse
 * @returns Boolean value
 */
export function parseBoolean(value: unknown, defaultValue: boolean = false): boolean {
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const lower = value.toLowerCase()
    if (lower === 'true' || lower === '1' || lower === 'yes') return true
    if (lower === 'false' || lower === '0' || lower === 'no') return false
  }
  if (typeof value === 'number') return value !== 0
  return defaultValue
}
