/**
 * Error Guard & Validation Helpers for Hono Routes
 */

import type { ZodSchema } from 'zod'
import { ZodError, z } from 'zod'
import {
  type HonoContext,
  type ErrorCode,
  HttpError,
  createError,
} from './error'

/**
 * Resource not found helper
 * Throws HttpError with NOT_FOUND code if value is null/undefined
 */
export function requireResource<T>(
  value: T | null | undefined,
  code: ErrorCode = 'NOT_FOUND',
  message: string = 'Resource not found'
): T {
  if (value === null || value === undefined) {
    throw new HttpError(code, message, undefined, 404)
  }
  return value
}

/**
 * Validate JSON body helper
 * Combines JSON parsing with zod validation in one call
 */
export async function validateJsonBody<T extends ZodSchema>(
  c: HonoContext,
  schema: T
): Promise<z.infer<T>> {
  try {
    const json = await c.req.json()
    return schema.parse(json)
  } catch (error) {
    if (error instanceof ZodError) {
      throw new HttpError('VALIDATION_ERROR', 'Validation failed', error.errors, 400)
    }
    if (error instanceof SyntaxError) {
      throw new HttpError('BAD_REQUEST', 'Invalid JSON', undefined, 400)
    }
    throw error
  }
}

/**
 * Empty array guard helper
 * Returns error response if array is empty
 */
export function guardEmptyArray<T>(
  arr: T[],
  c: HonoContext,
  message: string = 'No items found'
): T[] | Response {
  if (!arr || arr.length === 0) {
    return c.json(createError('NOT_FOUND', message), 404)
  }
  return arr
}

/**
 * D1 Database type for requireTenant helper
 */
export interface D1Database {
  prepare: (query: string) => {
    bind: (...params: unknown[]) => {
      first: () => Promise<unknown>
      run: () => Promise<{ success: boolean }>
      all: () => Promise<{ results: unknown[] }>
    }
  }
}

/**
 * Validate tenant exists helper
 * Checks if tenant exists in database, throws NOT_FOUND if not
 */
export async function requireTenant(
  db: D1Database,
  tenantId: string,
  message: string = 'Tenant not found'
): Promise<void> {
  const tenant = await db
    .prepare('SELECT id FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first()

  if (!tenant) {
    throw new HttpError('NOT_FOUND', message, undefined, 404)
  }
}

/**
 * Safe number parsing helper
 * Parses and validates number inputs with bounds checking
 */
export function safeNumber(
  value: unknown,
  min: number,
  max: number,
  defaultValue: number
): number {
  const parsed = typeof value === 'string' ? parseInt(value, 10) : Number(value ?? defaultValue)
  if (isNaN(parsed)) return defaultValue
  return Math.max(min, Math.min(max, parsed))
}

/**
 * Null-safe JSON parse helper
 * Safely parses JSON strings, returns fallback on failure
 */
export function safeJsonParse<T>(value: string | null | undefined, fallback: T): T {
  if (!value) return fallback
  try {
    return JSON.parse(value) as T
  } catch {
    return fallback
  }
}

/**
 * Get tenant from context with proper typing
 * Use this instead of c.get('tenant') to avoid 'unknown' type issues
 */
export function getTenant<B extends object | undefined = { tenant: unknown }>(c: HonoContext<B>): unknown {
  // @ts-expect-error - We know tenant is set by auth middleware
  return c.get('tenant')
}
