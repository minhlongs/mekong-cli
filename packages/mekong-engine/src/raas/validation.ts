import { z } from 'zod'
import type { Context } from 'hono'
import { createError } from '../types/error'

export const MAX_PAYLOAD_SIZE = 10_000 // 10KB

/**
 * Validates request body with Zod schema
 * Returns validated, typed body or throws error for handleAsync to catch
 */
export async function validateBody<T extends z.ZodType>(
  c: Context,
  schema: T
): Promise<z.infer<T>> {
  // Check content-length first
  const contentLength = c.req.header('content-length')
  if (!contentLength || parseInt(contentLength) > MAX_PAYLOAD_SIZE) {
    throw createError('PAYLOAD_TOO_LARGE', `Request body must be under ${MAX_PAYLOAD_SIZE} bytes`)
  }

  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    throw createError('INVALID_JSON', 'Request body must be valid JSON')
  }

  const result = schema.safeParse(json)
  if (!result.success) {
    throw createError('VALIDATION_ERROR', 'Validation failed', result.error.errors)
  }

  return result.data
}

/**
 * Validates request query parameters with Zod schema
 */
export function validateQuery<T extends z.ZodType>(
  c: Context,
  schema: T
): z.infer<T> {
  const result = schema.safeParse(c.req.query())
  if (!result.success) {
    throw createError('VALIDATION_ERROR', 'Query parameter validation failed', result.error.errors)
  }
  return result.data
}

/**
 * Validates route parameters with Zod schema
 */
export function validateParam<T extends z.ZodType>(
  c: Context,
  schema: T
): z.infer<T> {
  const result = schema.safeParse(c.req.param())
  if (!result.success) {
    throw createError('VALIDATION_ERROR', 'Route parameter validation failed', result.error.errors)
  }
  return result.data
}
