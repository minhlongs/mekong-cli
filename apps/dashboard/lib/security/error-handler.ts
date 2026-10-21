/**
 * Centralized Error Handling System
 * Standardized secure error responses with proper HTTP status codes
 */

import type { NextRequest, NextResponse } from 'next/server'
import type { z } from 'zod'
import { securityLogger } from './logger'
import {
  AuthenticationError,
  AuthorizationError,
  BadRequestError,
  BaseError,
  ConflictError,
  DatabaseError,
  type ErrorCategory,
  ErrorCategoryEnum,
  type ErrorCode,
  ErrorCodeEnum,
  ExternalServiceError,
  ForbiddenError,
  InsufficientPermissionsError,
  InternalError,
  NotFoundError,
  RateLimitedError,
  ResourceLimitError,
  SecurityViolationError,
  SubscriptionRequiredError,
  UnauthorizedError,
  ValidationError,
} from './error-types'
import {
  type ErrorHandlerConfig,
  type ErrorResponsePayload,
  extractRequestContext,
  formatErrorResponse,
  fromDatabaseError,
  fromExternalServiceError,
  fromRateLimitError,
  fromValidationError,
  generateRequestId,
} from './error-formatters'

export class ErrorHandler {
  private config: ErrorHandlerConfig

  constructor(config: Partial<ErrorHandlerConfig> = {}) {
    this.config = {
      includeStackTrace: process.env.NODE_ENV === 'development',
      includeContext: process.env.NODE_ENV === 'development',
      logAllErrors: true,
      sanitizeErrors: process.env.NODE_ENV === 'production',
      ...config,
    }
  }

  async handleError(error: Error, request?: NextRequest): Promise<NextResponse> {
    const requestId = generateRequestId()
    const requestContext = request ? extractRequestContext(request) : {}

    if (error instanceof BaseError) {
      await this.logError(error, requestContext)
      return formatErrorResponse(error, requestId, this.config)
    }

    const internalError = new InternalError(
      this.config.sanitizeErrors ? 'An error occurred' : error.message,
      error
    )

    await this.logError(internalError, { ...requestContext, originalError: error.message })
    return formatErrorResponse(internalError, requestId, this.config)
  }

  private async logError(error: BaseError, context: Record<string, unknown>): Promise<void> {
    if (!error.shouldLog && !this.config.logAllErrors) return

    const logData = {
      error: error.code,
      message: error.userMessage,
      category: error.category,
      statusCode: error.statusCode,
      context: error.context,
      requestContext: context,
      stack: error.stack,
    }

    if (error.category === 'SECURITY') {
      await securityLogger.security(
        'system_error',
        `${error.category}: ${error.userMessage}`,
        logData
      )
    } else if (error.category === 'CLIENT') {
      await securityLogger.warn(`Client error: ${error.userMessage}`, logData)
    } else {
      const errorMessage = error instanceof BaseError ? error.userMessage : 'Internal server error'
      await securityLogger.error(
        `Server error: ${errorMessage}`,
        error instanceof Error ? error : new Error(errorMessage),
        logData
      )
    }
  }

  static fromValidationError(zodError: z.ZodError): ValidationError {
    return fromValidationError(zodError)
  }

  static fromDatabaseError(error: unknown, operation: string): DatabaseError {
    return fromDatabaseError(error, operation)
  }

  static fromExternalServiceError(
    service: string,
    error: unknown,
    operation: string
  ): ExternalServiceError {
    return fromExternalServiceError(service, error, operation)
  }

  static fromRateLimitError(
    identifier: string,
    limitType: string,
    resetTime: Date
  ): RateLimitedError {
    return fromRateLimitError(identifier, limitType, resetTime)
  }
}

export const errorHandler = new ErrorHandler()

export function withErrorHandler<TContext = Record<string, unknown>>(
  handler: (request: NextRequest, context?: TContext) => Promise<NextResponse>
) {
  return async (request: NextRequest, context?: TContext): Promise<NextResponse> => {
    try {
      return await handler(request, context)
    } catch (error) {
      return await errorHandler.handleError(
        error instanceof Error ? error : new Error(String(error)),
        request
      )
    }
  }
}

export {
  AuthenticationError,
  AuthorizationError,
  BadRequestError,
  BaseError,
  ConflictError,
  DatabaseError,
  type ErrorCategory,
  ErrorCategoryEnum,
  type ErrorCode,
  ErrorCodeEnum,
  type ErrorHandlerConfig,
  type ErrorResponsePayload,
  ExternalServiceError,
  ForbiddenError,
  InsufficientPermissionsError,
  InternalError,
  NotFoundError,
  RateLimitedError,
  ResourceLimitError,
  SecurityViolationError,
  SubscriptionRequiredError,
  UnauthorizedError,
  ValidationError,
}
export default errorHandler
