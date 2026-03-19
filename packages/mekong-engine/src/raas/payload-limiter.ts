import type { Context } from 'hono'
import { createError } from '../types/error'

/**
 * Maximum payload size: 10KB
 * Prevents large payload DoS attacks
 */
export const MAX_PAYLOAD_SIZE = 10_000

/**
 * Middleware factory: Validate Content-Length header
 * Blocks requests with payload > MAX_PAYLOAD_SIZE
 * Usage: payloadSizeLimit() returns a middleware function
 */
export function payloadSizeLimit() {
  return async (c: Context, next: () => Promise<void>) => {
    const contentLength = c.req.header('content-length')

    if (contentLength) {
      const size = parseInt(contentLength, 10)
      if (isNaN(size)) {
        throw createError('BAD_REQUEST', 'Invalid Content-Length header')
      }
      if (size > MAX_PAYLOAD_SIZE) {
        throw createError(
          'PAYLOAD_TOO_LARGE',
          `Request body exceeds maximum size of ${MAX_PAYLOAD_SIZE} bytes`
        )
      }
    }

    await next()
  }
}

/**
 * Helper: Check payload size and parse JSON safely
 * Use this in route handlers instead of c.req.json() directly
 */
export async function parseJsonSafely(c: Context): Promise<unknown> {
  const contentLength = c.req.header('content-length')

  if (contentLength) {
    const size = parseInt(contentLength, 10)
    if (!isNaN(size) && size > MAX_PAYLOAD_SIZE) {
      throw createError(
        'PAYLOAD_TOO_LARGE',
        `Request body exceeds maximum size of ${MAX_PAYLOAD_SIZE} bytes`
      )
    }
  }

  try {
    return await c.req.json()
  } catch {
    throw createError('BAD_REQUEST', 'Invalid JSON payload')
  }
}
