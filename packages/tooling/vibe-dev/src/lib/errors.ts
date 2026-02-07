/**
 * Error types for vibe-dev CLI operations
 */

export class VibeDevError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly recoverable: boolean = false
  ) {
    super(message);
    this.name = 'VibeDevError';
  }
}

export class GitHubAPIError extends VibeDevError {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly rateLimitRemaining?: number
  ) {
    super(message, 'GITHUB_API_ERROR', statusCode === 403 || statusCode === 429);
    this.name = 'GitHubAPIError';
  }
}

export class StorageError extends VibeDevError {
  constructor(
    message: string,
    public readonly filePath: string
  ) {
    super(message, 'STORAGE_ERROR', false);
    this.name = 'StorageError';
  }
}

export class ValidationError extends VibeDevError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR', false);
    this.name = 'ValidationError';
  }
}

export class NetworkError extends VibeDevError {
  constructor(message: string) {
    super(message, 'NETWORK_ERROR', true);
    this.name = 'NetworkError';
  }
}

export class AuthenticationError extends VibeDevError {
  constructor(message: string) {
    super(message, 'AUTH_ERROR', false);
    this.name = 'AuthenticationError';
  }
}
