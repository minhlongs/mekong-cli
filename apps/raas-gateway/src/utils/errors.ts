/**
 * Custom error classes for API handling
 */

export class ApiError extends Error {
  constructor(
    public message: string,
    public status: number = 500,
    public code: string = 'INTERNAL_ERROR',
    public details?: Record<string, string>
  ) {
    super(message);
    this.name = 'ApiError';
  }

  toJSON() {
    return {
      error: this.message,
      code: this.code,
      details: this.details,
    };
  }
}

export class AuthenticationError extends ApiError {
  constructor(message = 'Authentication Required') {
    super(message, 401, 'AUTHENTICATION_REQUIRED');
  }
}

export class AuthorizationError extends ApiError {
  constructor(message = 'Access Denied') {
    super(message, 403, 'ACCESS_DENIED');
  }
}

export class RateLimitError extends ApiError {
  constructor(
    public message = 'Rate Limit Exceeded',
    public retryAfter?: number
  ) {
    super(message, 429, 'RATE_LIMIT_EXCEEDED');
  }
}

export class PaymentRequiredError extends ApiError {
  constructor(message = 'Insufficient Credits') {
    super(message, 402, 'PAYMENT_REQUIRED');
  }
}

export class ValidationError extends ApiError {
  constructor(
    message = 'Validation Failed',
    details?: Record<string, string>
  ) {
    super(message, 400, 'VALIDATION_ERROR', details);
  }
}
