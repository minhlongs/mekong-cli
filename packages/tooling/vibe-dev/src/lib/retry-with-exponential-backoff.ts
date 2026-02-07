/**
 * Retry utility with exponential backoff for handling transient failures
 */

import { NetworkError, GitHubAPIError } from './errors';

export interface RetryOptions {
  maxAttempts: number;
  initialDelay: number; // milliseconds
  maxDelay: number; // milliseconds
  backoffMultiplier: number;
  retryableErrors?: (error: Error) => boolean;
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  retryableErrors: (error: Error) => {
    // Retry on network errors or rate limit errors
    if (error instanceof NetworkError) return true;
    if (error instanceof GitHubAPIError) {
      return error.recoverable;
    }
    return false;
  }
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const opts = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: Error;
  let delay = opts.initialDelay;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;

      // Check if error is retryable
      if (!opts.retryableErrors || !opts.retryableErrors(error)) {
        throw error;
      }

      // If last attempt, throw
      if (attempt === opts.maxAttempts) {
        throw error;
      }

      // Log retry attempt
      console.warn(`Attempt ${attempt}/${opts.maxAttempts} failed: ${error.message}. Retrying in ${delay}ms...`);

      // Wait before retry
      await sleep(delay);

      // Exponential backoff
      delay = Math.min(delay * opts.backoffMultiplier, opts.maxDelay);
    }
  }

  // Should never reach here, but TypeScript needs it
  throw lastError!;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Rate limit handler for GitHub API
 */
export async function handleRateLimit(error: GitHubAPIError): Promise<void> {
  if (error.statusCode === 403 && error.rateLimitRemaining === 0) {
    const resetTime = 3600000; // 1 hour fallback
    console.warn(`Rate limit exceeded. Waiting ${resetTime / 1000}s before retry...`);
    await sleep(resetTime);
  } else if (error.statusCode === 429) {
    // Secondary rate limit - wait shorter period
    const waitTime = 60000; // 1 minute
    console.warn(`Secondary rate limit hit. Waiting ${waitTime / 1000}s...`);
    await sleep(waitTime);
  }
}
