/**
 * Standardized API Error Interface
 * All API endpoints MUST use this format for consistent error handling
 */

import type { Context, TypedResponse } from 'hono'
import type { Bindings } from '../index'
import type { ZodSchema } from 'zod'
import { ZodError, z } from 'zod'
import { logger } from '../lib/monitoring'

// Type alias for Hono context with our Bindings
export type HonoContext<B extends object | undefined = { tenant: unknown }> = Context<{ Bindings: Bindings; Variables: B }>

export const ERROR_CODES = {
  // Client Errors (4xx)
  BAD_REQUEST: 'BAD_REQUEST',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  REPLAY_ATTACK: 'REPLAY_ATTACK',
  INVALID_TIMESTAMP: 'INVALID_TIMESTAMP',
  INSUFFICIENT_CREDITS: 'INSUFFICIENT_CREDITS',
  VOTING_CLOSED: 'VOTING_CLOSED',
  DUPLICATE_ENTRY: 'DUPLICATE_ENTRY',
  PAYLOAD_TOO_LARGE: 'PAYLOAD_TOO_LARGE',
  INVALID_JSON: 'INVALID_JSON',

  // Server Errors (5xx)
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  DATABASE_ERROR: 'DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',
} as const

export type ErrorCode = keyof typeof ERROR_CODES

export interface ApiError {
  /** Human-readable error message */
  error: string
  /** Standardized error code for programmatic handling */
  code?: ErrorCode
  /** Zod validation errors or additional details */
  details?: unknown[]
  /** Optional HTTP status code (for server-side error construction) */
  status?: number
}

/**
 * Helper function to create standardized error responses
 * @param code - Error code from ERROR_CODES
 * @param message - Human-readable error message
 * @param details - Optional additional details (e.g., Zod errors)
 * @param status - Optional HTTP status code
 */
export function createError(
  code: ErrorCode,
  message: string,
  details?: unknown[],
  status?: number
): ApiError {
  return {
    error: message,
    code: ERROR_CODES[code],
    ...(details && { details }),
    ...(status && { status }),
  }
}

/**
 * Helper type for Hono error responses
 */
export type ErrorResponse = {
  json: ApiError
  status: number
}

/**
 * Custom Error class for HTTP errors
 * Use throw new HttpError('NOT_FOUND', 'Resource not found', 404)
 */
export class HttpError extends Error {
  public code: ErrorCode
  public status: number
  public details?: unknown[]

  constructor(code: ErrorCode, message: string, details?: unknown[], status?: number) {
    super(message)
    this.name = 'HttpError'
    this.code = code
    this.status = status || this.getDefaultStatus(code)
    this.details = details
  }

  private getDefaultStatus(code: ErrorCode): number {
    const clientErrors: ErrorCode[] = [
      'BAD_REQUEST', 'UNAUTHORIZED', 'FORBIDDEN', 'NOT_FOUND',
      'CONFLICT', 'VALIDATION_ERROR', 'REPLAY_ATTACK', 'INVALID_TIMESTAMP',
      'INSUFFICIENT_CREDITS', 'VOTING_CLOSED', 'DUPLICATE_ENTRY'
    ]
    return clientErrors.includes(code) ? 400 : 500
  }

  toResponse(): ApiError {
    return createError(this.code, this.message, this.details, this.status)
  }
}

/**
 * Type-safe async handler wrapper for Hono routes
 * Uses type assertion to work with any Hono Context type
 * The handler function receives the actual Hono Context with proper Bindings
 *
 * @example
 * ```ts
 * route.get('/users', handleAsync(async (c) => {
 *   const users = await db.getAll('SELECT * FROM users')
 *   return c.json({ users })
 * }))
 * ```
 */
export function handleAsync<B extends object | undefined = { tenant: unknown }, T = unknown>(
  fn: (c: HonoContext<B>) => Promise<T>
): (c: HonoContext<B>) => Promise<T | TypedResponse<unknown, any, string>> {
  return async (c: HonoContext<B>) => {
    try {
      return await fn(c)
    } catch (error) {
      if (error instanceof HttpError) {
        const response = error.toResponse()
        return c.json(response)
      }
      if (error instanceof ZodError) {
        return c.json(
          createError('VALIDATION_ERROR', 'Validation failed', error.errors),
          400
        )
      }
      // Unknown error - log and return 500
      logger.error('Unhandled error in route handler', { error: error instanceof Error ? error.message : String(error) })
      return c.json(
        createError('INTERNAL_ERROR', 'An unexpected error occurred'),
        500
      )
    }
  }
}

/**
 * Database operation error handler
 * Wraps D1 database calls with proper error handling
 *
 * @example
 * ```ts
 * const user = await handleDb(
 *   () => c.env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(id).first(),
 *   'DATABASE_ERROR',
 *   'Failed to fetch user'
 * )
 * ```
 */
export async function handleDb<T>(
  operation: () => Promise<T>,
  code: ErrorCode = 'DATABASE_ERROR',
  message: string = 'Database operation failed'
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    logger.error('Database error', { error: error instanceof Error ? error.message : String(error) })
    throw new HttpError(code, message, error instanceof Error ? [error.message] : undefined, 500)
  }
}

/**
 * External API call error handler
 * Wraps fetch/API calls with proper error handling
 *
 * @example
 * ```ts
 * const response = await handleExternalApi(
 *   () => fetch('https://api.example.com/data'),
 *   'External API call failed'
 * )
 * ```
 */
export async function handleExternalApi<T>(
  operation: () => Promise<T>,
  message: string = 'External service call failed'
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    logger.error('External API error', { error: error instanceof Error ? error.message : String(error) })
    throw new HttpError('EXTERNAL_SERVICE_ERROR', message, error instanceof Error ? [error.message] : undefined, 502)
  }
}

/**
 * Resource not found helper
 * Throws HttpError with NOT_FOUND code if value is null/undefined
 *
 * @example
 * ```ts
 * const user = await db.getUser(id)
 * return requireResource(user, 'NOT_FOUND', 'User not found')
 * ```
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
 *
 * @example
 * ```ts
 * const body = await validateJsonBody(c, createUserSchema)
 * ```
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
 *
 * @example
 * ```ts
 * const items = await getItems()
 * return guardEmptyArray(items, c, 'No items found')
 * ```
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
 *
 * @example
 * ```ts
 * const tenant = c.get('tenant')
 * await requireTenant(c.env.DB, tenant.id)
 * ```
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
 *
 * @example
 * ```ts
 * const limit = safeNumber(c.req.query('limit'), 1, 100, 50)
 * ```
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
 * Safely parses JSON strings, returns null on failure
 *
 * @example
 * ```ts
 * const tags = safeJsonParse(contact.tags, [])
 * ```
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
 *
 * @example
 * ```ts
 * const tenant = getTenant(c)
 * ```
 */
export function getTenant<B extends object | undefined = { tenant: unknown }>(c: HonoContext<B>): unknown {
  // @ts-expect-error - We know tenant is set by auth middleware
  return c.get('tenant')
}
