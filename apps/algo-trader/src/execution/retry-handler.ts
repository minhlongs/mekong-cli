export interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  factor: number; // Exponential backoff factor
  jitter: boolean; // Whether to add randomization to delays
  retryableErrors?: string[]; // Specific error messages that should trigger retries
}

export interface RetryMetrics {
  attempts: number;
  successfulRetries: number;
  totalRetryDelayMs: number;
}

export class RetryHandler {
  private metrics: RetryMetrics = {
    attempts: 0,
    successfulRetries: 0,
    totalRetryDelayMs: 0
  };

  constructor(private config: RetryConfig) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    let lastError: any;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      this.metrics.attempts++;

      try {
        const result = await operation();

        // If not the first attempt, increment successful retries counter
        if (attempt > 0) {
          this.metrics.successfulRetries++;
        }

        return result;
      } catch (error) {
        lastError = error;

        // If this is the last attempt, don't retry
        if (attempt === this.config.maxRetries) {
          break;
        }

        // Check if this error is retryable
        if (!this.shouldRetry(error)) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = this.calculateDelay(attempt);
        this.metrics.totalRetryDelayMs += delay;

        // Wait before retrying
        await this.sleep(delay);
      }
    }

    throw lastError;
  }

  private calculateDelay(attempt: number): number {
    let delay = this.config.baseDelayMs * Math.pow(this.config.factor, attempt);

    // Cap the delay at maxDelayMs
    delay = Math.min(delay, this.config.maxDelayMs);

    // Add jitter if enabled
    if (this.config.jitter) {
      delay = delay * (0.5 + Math.random() * 0.5); // Randomize between 50-100% of calculated delay
    }

    return delay;
  }

  private shouldRetry(error: any): boolean {
    // If specific retryable errors are defined, check against them
    if (this.config.retryableErrors && this.config.retryableErrors.length > 0) {
      const errorMessage = error.message ? error.message.toLowerCase() : '';
      return this.config.retryableErrors.some(retryableError =>
        errorMessage.includes(retryableError.toLowerCase())
      );
    }

    // Default behavior: retry on network-related errors
    const errorMessage = error.message ? error.message.toLowerCase() : '';
    const retryableKeywords = [
      'network error',
      'timeout',
      'connection refused',
      'rate limit',
      'too many requests',
      '5xx',
      'internal server error',
      'gateway timeout',
      'service unavailable'
    ];

    return retryableKeywords.some(keyword =>
      errorMessage.includes(keyword)
    );
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getMetrics(): RetryMetrics {
    return { ...this.metrics };
  }

  resetMetrics(): void {
    this.metrics = {
      attempts: 0,
      successfulRetries: 0,
      totalRetryDelayMs: 0
    };
  }
}