/**
 * Standardized API Error Interface
 * All API endpoints MUST use this format for consistent error handling
 */

import type { Context, TypedResponse } from 'hono'
import type { ContentfulStatusCode } from 'hono/utils/http-status'
import type { Bindings } from '../index'
import { ZodError } from 'zod'
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
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',

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
 */
export function handleAsync<B extends object | undefined = { tenant: unknown }, T = unknown>(
  fn: (c: HonoContext<B>) => Promise<T>
): (c: HonoContext<B>) => Promise<T | TypedResponse<unknown, ContentfulStatusCode, string>> {
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

export type { D1Database } from './error-helpers'
export {
  requireResource,
  validateJsonBody,
  guardEmptyArray,
  requireTenant,
  safeNumber,
  safeJsonParse,
  getTenant,
} from './error-helpers'
