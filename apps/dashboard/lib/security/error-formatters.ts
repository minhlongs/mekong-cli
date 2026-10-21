/**
 * Error Response Formatters & Error Factory Helpers
 */

import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import type { z } from 'zod'
import {
  type BaseError,
  DatabaseError,
  type ErrorCode,
  ExternalServiceError,
  RateLimitedError,
  ValidationError,
} from './error-types'

export interface ErrorHandlerConfig {
  includeStackTrace: boolean
  includeContext: boolean
  logAllErrors: boolean
  sanitizeErrors: boolean
}

export interface ErrorResponsePayload {
  error: ErrorCode
  message: string
  requestId: string
  timestamp: string
  context?: Record<string, unknown>
  stack?: string
}

export function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export function extractRequestContext(request: NextRequest): Record<string, unknown> {
  return {
    method: request.method,
    url: request.url,
    userAgent: request.headers.get('user-agent'),
    ip: request.headers.get('x-forwarded-for')?.split(',')[0] || request.headers.get('x-real-ip'),
    userId: request.headers.get('x-user-id'),
    sessionId: request.headers.get('x-session-id'),
  }
}

export function formatErrorResponse(
  error: BaseError,
  requestId: string,
  config: ErrorHandlerConfig
): NextResponse {
  const response: ErrorResponsePayload = {
    error: error.code,
    message: error.userMessage,
    requestId,
    timestamp: new Date().toISOString(),
  }

  if (config.includeContext && error.context) {
    response.context = error.context
  }

  if (config.includeStackTrace && error.stack) {
    response.stack = error.stack
  }

  return NextResponse.json(response, {
    status: error.statusCode,
    headers: {
      'X-Request-ID': requestId,
      'X-Error-Code': error.code,
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
    },
  })
}

export function fromValidationError(zodError: z.ZodError): ValidationError {
  const fieldErrors = zodError.errors.map(err => ({
    field: err.path.join('.'),
    message: err.message,
    code: err.code,
  }))

  return new ValidationError('Input validation failed', { fieldErrors })
}

export function fromDatabaseError(error: unknown, operation: string): DatabaseError {
  const errObj =
    typeof error === 'object' && error !== null
      ? (error as { message?: string; code?: string })
      : {}
  const sanitizedError = {
    operation,
    message: errObj.message?.substring(0, 100) || 'Unknown database error',
    code: errObj.code,
  }

  return new DatabaseError(`Database ${operation} failed`, sanitizedError)
}

export function fromExternalServiceError(
  service: string,
  _error: unknown,
  operation: string
): ExternalServiceError {
  return new ExternalServiceError(service, `${service} ${operation} failed`)
}

export function fromRateLimitError(
  identifier: string,
  limitType: string,
  resetTime: Date
): RateLimitedError {
  return new RateLimitedError(`Rate limit exceeded for ${limitType}`, {
    identifier: identifier.substring(0, 10) + '***',
    limitType,
    resetTime: resetTime.toISOString(),
  })
}
