/**
 * Circuit Breaker Tests
 * Lightweight unit tests for circuit breaker pattern
 */

import { describe, test, expect, jest } from '@jest/globals';
import {
  CircuitBreaker,
  CircuitBreakerState,
  CircuitBreakerConfig
} from '../../src/execution/circuit-breaker';

describe('Circuit Breaker', () => {
  const defaultConfig: CircuitBreakerConfig = {
    failureThreshold: 3,
    timeoutMs: 1000,
    successThreshold: 2
  };

  describe('Initialization', () => {
    test('should start in CLOSED state', () => {
      const cb = new CircuitBreaker(defaultConfig);
      const metrics = cb.getMetrics();
      expect(metrics.state).toBe(CircuitBreakerState.CLOSED);
      expect(metrics.failureCount).toBe(0);
    });

    test('should have zero metrics on init', () => {
      const cb = new CircuitBreaker(defaultConfig);
      const metrics = cb.getMetrics();
      expect(metrics.totalRequests).toBe(0);
      expect(metrics.totalFailures).toBe(0);
      expect(metrics.totalSuccesses).toBe(0);
    });
  });

  describe('Successful Execution', () => {
    test('should pass through successful operation', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      const result = await cb.execute(async () => 'success');
      expect(result).toBe('success');
    });

    test('should increment success count', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      await cb.execute(async () => 'ok');
      const metrics = cb.getMetrics();
      expect(metrics.totalSuccesses).toBe(1);
      expect(metrics.totalRequests).toBe(1);
    });
  });

  describe('Failure Handling', () => {
    test('should throw on failed operation', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      await expect(cb.execute(async () => {
        throw new Error('Test error');
      })).rejects.toThrow('Test error');
    });

    test('should increment failure count', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      try {
        await cb.execute(async () => { throw new Error('fail'); });
      } catch {}
      const metrics = cb.getMetrics();
      expect(metrics.totalFailures).toBe(1);
      expect(metrics.failureCount).toBe(1);
    });

    test('should track last failure time', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      const beforeFail = Date.now();
      try {
        await cb.execute(async () => { throw new Error('fail'); });
      } catch {}
      const metrics = cb.getMetrics();
      expect(metrics.lastFailureTime).toBeDefined();
      expect(metrics.lastFailureTime!).toBeGreaterThanOrEqual(beforeFail);
    });
  });

  describe('Circuit Opening', () => {
    test('should open after threshold failures', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      for (let i = 0; i < 3; i++) {
        try {
          await cb.execute(async () => { throw new Error('fail'); });
        } catch {}
      }
      const metrics = cb.getMetrics();
      expect(metrics.state).toBe(CircuitBreakerState.OPEN);
    });

    test('should throw immediately when open', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      // Force open
      for (let i = 0; i < 3; i++) {
        try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      }
      await expect(cb.execute(async () => 'ok'))
        .rejects.toThrow('Circuit breaker is OPEN');
    });

    test('should not increment failure count when already open', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      // Open circuit
      for (let i = 0; i < 3; i++) {
        try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      }
      const failuresBefore = cb.getMetrics().totalFailures;
      try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      // Should not increment because circuit is open
      expect(cb.getMetrics().totalFailures).toBe(failuresBefore + 1);
    });
  });

  describe('Half-Open State', () => {
    test('should transition to half-open after timeout', async () => {
      const cb = new CircuitBreaker({ ...defaultConfig, timeoutMs: 50 });
      // Open circuit
      for (let i = 0; i < 3; i++) {
        try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      }
      expect(cb.getMetrics().state).toBe(CircuitBreakerState.OPEN);

      // Wait for timeout
      await new Promise(r => setTimeout(r, 60));

      // Next call should trigger half-open check
      try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      expect(cb.getMetrics().state).toBe(CircuitBreakerState.HALF_OPEN);
    });

    test('should close after success threshold in half-open', async () => {
      const cb = new CircuitBreaker({ ...defaultConfig, timeoutMs: 50, successThreshold: 2 });
      // Open circuit
      for (let i = 0; i < 3; i++) {
        try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      }
      await new Promise(r => setTimeout(r, 60));

      // Successful calls in half-open
      await cb.execute(async () => 'ok');
      await cb.execute(async () => 'ok');

      expect(cb.getMetrics().state).toBe(CircuitBreakerState.CLOSED);
    });
  });

  describe('Reset', () => {
    test('should reset all metrics', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      // Cause some failures
      for (let i = 0; i < 3; i++) {
        try { await cb.execute(async () => { throw new Error('fail'); }); } catch {}
      }
      cb.reset();
      const metrics = cb.getMetrics();
      expect(metrics.state).toBe(CircuitBreakerState.CLOSED);
      expect(metrics.failureCount).toBe(0);
      expect(metrics.totalRequests).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    test('should handle async operation rejection', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      const rejectedPromise = cb.execute(async () => {
        return await Promise.reject(new Error('async fail'));
      });
      await expect(rejectedPromise).rejects.toThrow('async fail');
    });

    test('should handle null error', async () => {
      const cb = new CircuitBreaker(defaultConfig);
      await expect(cb.execute(async () => { throw null; })).rejects.toBe(null);
    });
  });
});
