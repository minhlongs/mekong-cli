
export enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

export interface CircuitBreakerConfig {
  failureThreshold: number; // Number of failures before opening circuit
  timeoutMs: number; // Time to wait before trying again (ms)
  successThreshold: number; // Successes needed to close circuit after half-open
}

export interface CircuitBreakerMetrics {
  state: CircuitBreakerState;
  failureCount: number;
  successCount: number;
  lastFailureTime: number | null;
  totalRequests: number;
  totalFailures: number;
  totalSuccesses: number;
}

export class CircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failureCount: number = 0;
  private successCount: number = 0;
  private lastFailureTime: number | null = null;
  private totalRequests: number = 0;
  private totalFailures: number = 0;
  private totalSuccesses: number = 0;

  private openedAt: number | null = null;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    this.totalRequests++;

    // Check if we should attempt to reset the circuit
    if (this.state === CircuitBreakerState.OPEN && this.isTimeoutExceeded()) {
      this.halfOpen();
    }

    // If circuit is open, fail fast
    if (this.state === CircuitBreakerState.OPEN) {
      throw new Error(`Circuit breaker is OPEN. Last failure: ${this.lastFailureTime}`);
    }

    try {
      const result = await operation();

      // Operation succeeded
      this.onSuccess();
      return result;
    } catch (error) {
      // Operation failed
      this.onFailure(error);
      throw error;
    }
  }

  private onSuccess(): void {
    this.totalSuccesses++;

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.successCount++;

      if (this.successCount >= this.config.successThreshold) {
        this.close(); // Close circuit after sufficient successes in half-open state
      }
    } else if (this.state === CircuitBreakerState.CLOSED) {
      this.successCount = 0; // Reset success count in closed state
    }
  }

  private onFailure(error: any): void {
    this.totalFailures++;
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.config.failureThreshold) {
      this.open(); // Open circuit after too many failures
    }
  }

  private open(): void {
    this.state = CircuitBreakerState.OPEN;
    this.openedAt = Date.now();
    this.successCount = 0; // Reset success count when opening
  }

  private halfOpen(): void {
    this.state = CircuitBreakerState.HALF_OPEN;
    this.failureCount = 0; // Reset failure count when going half-open
  }

  private close(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.openedAt = null;
  }

  private isTimeoutExceeded(): boolean {
    if (!this.openedAt) return false;
    return Date.now() - this.openedAt >= this.config.timeoutMs;
  }

  reset(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
    this.totalRequests = 0;
    this.totalFailures = 0;
    this.totalSuccesses = 0;
    this.openedAt = null;
  }

  getMetrics(): CircuitBreakerMetrics {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
      totalRequests: this.totalRequests,
      totalFailures: this.totalFailures,
      totalSuccesses: this.totalSuccesses
    };
  }
}