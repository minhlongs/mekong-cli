/**
 * Response helpers for consistent API responses
 */

export interface ApiError {
  error: string;
  code?: string;
  details?: Record<string, string>;
}

export function json<T>(data: T, init?: ResponseInit): Response {
  return Response.json(data, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });
}

export function errorResponse(error: ApiError, status: number): Response {
  return json(error, { status });
}

export function notFound(message = 'Not Found'): Response {
  return errorResponse({ error: message, code: 'NOT_FOUND' }, 404);
}

export function methodNotAllowed(allowed: string[]): Response {
  return errorResponse({
    error: 'Method Not Allowed',
    code: 'METHOD_NOT_ALLOWED',
    details: { allowed: allowed.join(', ') }
  }, 405);
}

export function internalError(message = 'Internal Server Error'): Response {
  return errorResponse({ error: message, code: 'INTERNAL_ERROR' }, 500);
}
