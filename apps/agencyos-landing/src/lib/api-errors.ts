import { NextResponse } from 'next/server';
import { z } from 'zod';

type ApiErrorResponse = {
  error: string;
  code: string;
  details?: z.ZodIssue[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
    public readonly details?: z.ZodIssue[]
  ) {
    super(message);
    this.name = 'ApiError';
  }

  toResponse(): NextResponse<ApiErrorResponse> {
    const body: ApiErrorResponse = { error: this.message, code: this.code };
    if (this.details) body.details = this.details;
    return NextResponse.json(body, { status: this.status });
  }
}

export function handleRouteError(error: unknown): NextResponse<ApiErrorResponse> {
  if (error instanceof ApiError) {
    return error.toResponse();
  }

  if (error instanceof z.ZodError) {
    return new ApiError(
      'Invalid request data',
      'VALIDATION_ERROR',
      400,
      error.issues
    ).toResponse();
  }

  if (error instanceof SyntaxError) {
    return new ApiError('Malformed JSON body', 'INVALID_JSON', 400).toResponse();
  }

  return new ApiError(
    'Internal server error',
    'INTERNAL_ERROR',
    500
  ).toResponse();
}
