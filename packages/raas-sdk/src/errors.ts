/**
 * Error classes for Mekong RaaS SDK
 */

export class MekongApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = 'MekongApiError';
    this.status = status;
    this.code = code;
  }
}

export class MekongAuthError extends MekongApiError {
  constructor(message = 'Authentication required') {
    super(message, 401, 'UNAUTHORIZED');
    this.name = 'MekongAuthError';
  }
}

export class MekongInsufficientCreditsError extends MekongApiError {
  constructor(message = 'Insufficient credits') {
    super(message, 402, 'INSUFFICIENT_CREDITS');
    this.name = 'MekongInsufficientCreditsError';
  }
}

export class MekongNotFoundError extends MekongApiError {
  constructor(message = 'Resource not found') {
    super(message, 404, 'NOT_FOUND');
    this.name = 'MekongNotFoundError';
  }
}

export class MekongRateLimitError extends MekongApiError {
  constructor(message = 'Rate limit exceeded') {
    super(message, 429, 'RATE_LIMITED');
    this.name = 'MekongRateLimitError';
  }
}

export class MekongNetworkError extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
    this.name = 'MekongNetworkError';
  }
}

/** Map HTTP status code to typed error */
export function createApiError(status: number, body: { error?: string; code?: string }): MekongApiError {
  const message = body.error ?? 'Unknown error';
  const code = body.code ?? String(status);

  if (status === 401) return new MekongAuthError(message);
  if (status === 402) return new MekongInsufficientCreditsError(message);
  if (status === 404) return new MekongNotFoundError(message);
  if (status === 429) return new MekongRateLimitError(message);
  return new MekongApiError(message, status, code);
}
