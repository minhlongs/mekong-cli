/**
 * Centralized Input Validation Middleware
 * Comprehensive input sanitization and validation rules
 */

import type { NextRequest, NextResponse } from 'next/server'
import { NextResponse as NextResponseClass } from 'next/server'
import { z } from 'zod'
import { securityLogger } from './logger'
import { commonSchemas } from './validation-schemas'
import { InputValidationError, SecurityValidator } from './validation-helpers'

export interface ValidationConfig<
  TBody extends z.ZodSchema = z.ZodSchema,
  TQuery extends z.ZodSchema = z.ZodSchema,
  TParams extends z.ZodSchema = z.ZodSchema,
  THeaders extends z.ZodSchema = z.ZodSchema,
> {
  body?: TBody
  query?: TQuery
  params?: TParams
  headers?: THeaders
  requireAuth?: boolean
  sanitizeInput?: boolean
}

export interface ValidatedData<
  TBody = unknown,
  TQuery = unknown,
  TParams = unknown,
  THeaders = unknown,
> {
  body?: TBody
  query?: TQuery
  params?: TParams
  headers?: THeaders
}

export function createValidationMiddleware<
  TBody extends z.ZodSchema = z.ZodSchema,
  TQuery extends z.ZodSchema = z.ZodSchema,
  TParams extends z.ZodSchema = z.ZodSchema,
  THeaders extends z.ZodSchema = z.ZodSchema,
>(config: ValidationConfig<TBody, TQuery, TParams, THeaders>) {
  type ResultData = ValidatedData<z.infer<TBody>, z.infer<TQuery>, z.infer<TParams>, z.infer<THeaders>>
  return async (
    request: NextRequest,
    context: { params?: Record<string, string> } = {}
  ): Promise<{ success: true; data: ResultData } | { success: false; error: NextResponse }> => {
    try {
      const validatedData: ResultData = {}

      if (config.body && ['POST', 'PUT', 'PATCH'].includes(request.method)) {
        try {
          validatedData.body = config.body.parse(await request.json())
        } catch (err) {
          if (err instanceof z.ZodError) throw err
          return {
            success: false,
            error: NextResponseClass.json({ error: 'Invalid JSON in request body' }, { status: 400 }),
          }
        }
      }

      if (config.query) {
        validatedData.query = config.query.parse(Object.fromEntries(request.nextUrl.searchParams))
      }

      if (config.params && context.params) {
        validatedData.params = config.params.parse(context.params)
      }

      if (config.headers) {
        const headers: Record<string, string> = {}
        request.headers.forEach((value, key) => {
          headers[key.toLowerCase().replace(/-/g, '_')] = value
        })
        validatedData.headers = config.headers.parse(headers)
      }

      if (config.sanitizeInput !== false) {
        const allValues = JSON.stringify({
          body: validatedData.body,
          query: validatedData.query,
          params: validatedData.params,
        })
        const [sqlSafe, xssSafe, cmdSafe] = await Promise.all([
          SecurityValidator.validateSqlInjection(allValues),
          SecurityValidator.validateXss(allValues),
          SecurityValidator.validateCommandInjection(allValues),
        ])
        if (!sqlSafe || !xssSafe || !cmdSafe) {
          return {
            success: false,
            error: NextResponseClass.json({ error: 'Invalid input detected' }, { status: 400 }),
          }
        }
      }

      if (config.requireAuth) {
        if (!request.headers.get('authorization') && !request.headers.get('x-user-id')) {
          await securityLogger.authorization(false, 'anonymous', request.url, 'access')
          return {
            success: false,
            error: NextResponseClass.json({ error: 'Authentication required' }, { status: 401 }),
          }
        }
      }

      return { success: true, data: validatedData }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = error.errors.map(err => ({
          field: err.path.join('.'),
          message: err.message,
          code: err.code,
        }))
        await securityLogger.security('malicious_request', 'Validation failed', { errors: fieldErrors })
        return {
          success: false,
          error: NextResponseClass.json({ error: 'Validation failed', details: fieldErrors }, { status: 400 }),
        }
      }
      await securityLogger.error(
        'Validation middleware error',
        error instanceof Error ? error : new Error(String(error))
      )
      return {
        success: false,
        error: NextResponseClass.json({ error: 'Internal server error' }, { status: 500 }),
      }
    }
  }
}

export const validatePagination = createValidationMiddleware({
  query: z.object({
    page: commonSchemas.page,
    limit: commonSchemas.limit,
    sortBy: commonSchemas.sortBy.optional(),
    sortOrder: commonSchemas.sortOrder.optional(),
  }),
})
export const validateUserId = createValidationMiddleware({ params: z.object({ userId: commonSchemas.uuid }) })
export const validateAuth = createValidationMiddleware({ requireAuth: true })
export const validateEmailUpdate = createValidationMiddleware({
  body: z.object({ email: commonSchemas.email }),
  requireAuth: true,
})
export const validatePasswordChange = createValidationMiddleware({
  body: z.object({ currentPassword: commonSchemas.nonEmptyString, newPassword: commonSchemas.password }),
  requireAuth: true,
})
export const validateFileUpload = createValidationMiddleware({
  body: z.object({
    fileName: commonSchemas.fileName,
    fileSize: commonSchemas.fileSize,
    mimeType: commonSchemas.mimeType,
  }),
})

export { commonSchemas, SecurityValidator, InputValidationError, InputValidationError as ValidationError }
export default {
  createValidationMiddleware,
  commonSchemas,
  validatePagination,
  validateUserId,
  validateAuth,
  validateEmailUpdate,
  validatePasswordChange,
  validateFileUpload,
}
