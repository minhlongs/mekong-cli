/**
 * Standardized Security & Application Error Classes
 */

import { z } from 'zod'

export const ErrorCodeEnum = z.enum([
  'BAD_REQUEST', 'UNAUTHORIZED', 'FORBIDDEN', 'NOT_FOUND', 'METHOD_NOT_ALLOWED', 'CONFLICT',
  'VALIDATION_ERROR', 'RATE_LIMITED', 'PAYLOAD_TOO_LARGE', 'UNSUPPORTED_MEDIA_TYPE',
  'INTERNAL_ERROR', 'SERVICE_UNAVAILABLE', 'DATABASE_ERROR', 'EXTERNAL_SERVICE_ERROR',
  'TIMEOUT', 'SECURITY_VIOLATION', 'AUTHENTICATION_FAILED', 'AUTHORIZATION_FAILED',
  'TOKEN_EXPIRED', 'INVALID_TOKEN', 'CSRF_INVALID', 'INSUFFICIENT_PERMISSIONS',
  'RESOURCE_LIMIT_EXCEEDED', 'SUBSCRIPTION_REQUIRED', 'QUOTA_EXCEEDED', 'ACCOUNT_SUSPENDED',
])
export type ErrorCode = z.infer<typeof ErrorCodeEnum>

export const ErrorCategoryEnum = z.enum(['CLIENT', 'SERVER', 'SECURITY', 'BUSINESS', 'EXTERNAL'])
export type ErrorCategory = z.infer<typeof ErrorCategoryEnum>

export abstract class BaseError extends Error {
  public readonly code: ErrorCode
  public readonly category: ErrorCategory
  public readonly statusCode: number
  public readonly userMessage: string
  public readonly context?: Record<string, unknown>
  public readonly shouldLog: boolean
  public readonly requestId?: string

  constructor(
    code: ErrorCode,
    userMessage: string,
    statusCode: number = 500,
    category: ErrorCategory = 'SERVER',
    context?: Record<string, unknown>,
    shouldLog: boolean = true,
    requestId?: string
  ) {
    super(userMessage)
    this.name = this.constructor.name
    this.code = code
    this.category = category
    this.statusCode = statusCode
    this.userMessage = userMessage
    this.context = context
    this.shouldLog = shouldLog
    this.requestId = requestId
    if (Error.captureStackTrace) Error.captureStackTrace(this, this.constructor)
  }

  toJSON() {
    return {
      error: this.code,
      message: this.userMessage,
      requestId: this.requestId,
      timestamp: new Date().toISOString(),
    }
  }
}

export class BadRequestError extends BaseError {
  constructor(message: string = 'Bad request', context?: Record<string, unknown>) {
    super('BAD_REQUEST', message, 400, 'CLIENT', context)
  }
}

export class UnauthorizedError extends BaseError {
  constructor(message: string = 'Authentication required', context?: Record<string, unknown>) {
    super('UNAUTHORIZED', message, 401, 'SECURITY', context)
  }
}

export class ForbiddenError extends BaseError {
  constructor(message: string = 'Access denied', context?: Record<string, unknown>) {
    super('FORBIDDEN', message, 403, 'SECURITY', context)
  }
}

export class NotFoundError extends BaseError {
  constructor(resource: string = 'Resource') {
    super('NOT_FOUND', `${resource} not found`, 404, 'CLIENT')
  }
}

export class ConflictError extends BaseError {
  constructor(message: string = 'Resource conflict', context?: Record<string, unknown>) {
    super('CONFLICT', message, 409, 'CLIENT', context)
  }
}

export class ValidationError extends BaseError {
  constructor(message: string = 'Validation failed', context?: Record<string, unknown>) {
    super('VALIDATION_ERROR', message, 400, 'CLIENT', context)
  }
}

export class RateLimitedError extends BaseError {
  constructor(message: string = 'Rate limit exceeded', context?: Record<string, unknown>) {
    super('RATE_LIMITED', message, 429, 'SECURITY', context)
  }
}

export class InternalError extends BaseError {
  constructor(message: string = 'Internal server error', originalError?: Error) {
    super('INTERNAL_ERROR', message, 500, 'SERVER', {
      originalError: originalError?.message,
      stack: process.env.NODE_ENV === 'development' ? originalError?.stack : undefined,
    })
  }
}

export class DatabaseError extends BaseError {
  constructor(message: string = 'Database operation failed', context?: Record<string, unknown>) {
    super('DATABASE_ERROR', message, 500, 'SERVER', context)
  }
}

export class ExternalServiceError extends BaseError {
  constructor(service: string, message: string = 'External service error') {
    super('EXTERNAL_SERVICE_ERROR', message, 502, 'EXTERNAL', { service })
  }
}

export class SecurityViolationError extends BaseError {
  constructor(message: string = 'Security violation detected', context?: Record<string, unknown>) {
    super('SECURITY_VIOLATION', message, 400, 'SECURITY', context)
  }
}

export class AuthenticationError extends BaseError {
  constructor(message: string = 'Authentication failed', context?: Record<string, unknown>) {
    super('AUTHENTICATION_FAILED', message, 401, 'SECURITY', context)
  }
}

export class AuthorizationError extends BaseError {
  constructor(resource: string, action: string) {
    super('AUTHORIZATION_FAILED', `Cannot ${action} ${resource}`, 403, 'SECURITY', { resource, action })
  }
}

export class InsufficientPermissionsError extends BaseError {
  constructor(permission: string) {
    super('INSUFFICIENT_PERMISSIONS', `Insufficient permissions: ${permission}`, 403, 'BUSINESS', { permission })
  }
}

export class ResourceLimitError extends BaseError {
  constructor(limit: string, current: number) {
    super('RESOURCE_LIMIT_EXCEEDED', `Resource limit exceeded: ${limit}`, 429, 'BUSINESS', { limit, current })
  }
}

export class SubscriptionRequiredError extends BaseError {
  constructor(feature: string) {
    super('SUBSCRIPTION_REQUIRED', `Subscription required for ${feature}`, 402, 'BUSINESS', { feature })
  }
}
