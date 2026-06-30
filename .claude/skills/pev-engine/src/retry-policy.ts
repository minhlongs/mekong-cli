/**
 * PEV Engine — Retry Policy
 *
 * Port of Mekong CLI's RetryPolicy.
 * Temporal-inspired exponential backoff with full jitter.
 */

export type BackoffStrategy = 'fixed' | 'exponential' | 'full_jitter';

export interface RetryPolicy {
  max_attempts: number;
  initial_interval_ms: number;
  backoff: BackoffStrategy;
  max_interval_ms: number;
  non_retryable_exit_codes: number[];
}

export const DEFAULT_RETRY_POLICY: Readonly<RetryPolicy> = {
  max_attempts: 3,
  initial_interval_ms: 1000,
  backoff: 'exponential',
  max_interval_ms: 60000,
  non_retryable_exit_codes: [2],
};

export function isRetryable(policy: RetryPolicy, exitCode: number, stderr: string): boolean {
  // Non-retryable exit codes (e.g., 2 = bad input)
  if (policy.non_retryable_exit_codes.includes(exitCode)) return false;

  // Retry on network/timeout errors
  const retryablePatterns = [
    /timeout/i,
    /ECONNREFUSED/i,
    /ECONNRESET/i,
    /ETIMEDOUT/i,
    /502/i,
    /503/i,
    /504/i,
    /temporarily unavailable/i,
  ];

  return retryablePatterns.some(pattern => pattern.test(stderr));
}

export function computeBackoffDelay(
  policy: RetryPolicy,
  attempt: number,
): number {
  const { initial_interval_ms, backoff, max_interval_ms } = policy;
  let delay: number;

  switch (backoff) {
    case 'fixed':
      delay = initial_interval_ms;
      break;
    case 'exponential':
      delay = initial_interval_ms * Math.pow(2, attempt - 1);
      break;
    case 'full_jitter':
      delay = Math.random() * Math.min(initial_interval_ms * Math.pow(2, attempt - 1), max_interval_ms);
      break;
    default:
      delay = initial_interval_ms;
  }

  return Math.min(delay, max_interval_ms);
}

export function mergeRetryPolicy(
  base: RetryPolicy,
  override?: Partial<RetryPolicy>,
): RetryPolicy {
  if (!override) return base;
  return { ...base, ...override };
}
