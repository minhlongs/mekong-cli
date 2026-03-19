/**
 * Standardized API Error Interface
 * All API endpoints MUST use this format for consistent error handling
 */

import type { ZodSchema } from 'zod'

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
 * Automatically catches errors and returns proper format
 *
 * @example
 * ```ts
 * route.get('/users', handleAsync(async (c) => {
 *   const users = await db.getAll('SELECT * FROM users')
 *   return c.json({ users })
 * }))
 * ```
 */
export function handleAsync<T>(
  fn: (c: any) => Promise<T>
): (c: any) => Promise<T | Response> {
  return async (c: any) => {
    try {
      return await fn(c)
    } catch (error) {
      if (error instanceof HttpError) {
        return c.json(error.toResponse(), error.status)
      }
      if (error instanceof ZodError) {
        return c.json(
          createError('VALIDATION_ERROR', 'Validation failed', error.errors),
          400
        )
      }
      // Unknown error - log and return 500
      console.error('Unhandled error in route handler:', error)
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
    console.error('Database error:', error)
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
    console.error('External API error:', error)
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
  c: any,
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
  c: any,
  message: string = 'No items found'
): T[] | Response {
  if (!arr || arr.length === 0) {
    return c.json(createError('NOT_FOUND', message), 404)
  }
  return arr
}
