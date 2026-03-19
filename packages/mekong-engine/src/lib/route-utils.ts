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

