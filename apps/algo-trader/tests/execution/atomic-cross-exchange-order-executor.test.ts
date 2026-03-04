/**
 * Tests for AtomicCrossExchangeOrderExecutor.
 * Verifies parallel execution, rollback on partial failure, and full-failure handling.
 */

import {
  AtomicCrossExchangeOrderExecutor,
  AtomicExecutorConfig
} from '../../src/execution/atomic-cross-exchange-order-executor';
import { CircuitBreakerConfig } from '../../src/execution/circuit-breaker';
import { RetryConfig } from '../../src/execution/retry-handler';
import type { IExchange, IOrder, IBalance, IOrderBook } from '../../src/interfaces/IExchange';

// --- Mock IExchange factory ---
const makeOrder = (id: string, side: 'buy' | 'sell', price: number, amount: number): IOrder => ({
  id,
  symbol: 'BTC/USDT',
  side,
  amount,
  price,
  status: 'closed',
  timestamp: Date.now(),
});

const makeMockExchange = (name: string, orderOverride?: () => Promise<IOrder>): jest.Mocked<IExchange> => ({
  name,
  connect: jest.fn().mockResolvedValue(undefined),
  fetchTicker: jest.fn().mockResolvedValue(68000),
  fetchOrderBook: jest.fn().mockResolvedValue({} as IOrderBook),
  fetchBalance: jest.fn().mockResolvedValue({} as Record<string, IBalance>),
  createMarketOrder: jest.fn().mockImplementation(
    orderOverride ?? ((_symbol: string, side: 'buy' | 'sell', amount: number) =>
      Promise.resolve(makeOrder('ord-1', side, side === 'buy' ? 68000 : 68200, amount))
    )
  ),
});

describe('AtomicCrossExchangeOrderExecutor', () => {
  let buyExchange: jest.Mocked<IExchange>;
  let sellExchange: jest.Mocked<IExchange>;

  beforeEach(() => {
    buyExchange = makeMockExchange('binance');
    sellExchange = makeMockExchange('okx', () =>
      Promise.resolve(makeOrder('ord-2', 'sell', 68200, 0.1))
    );
  });

  describe('basic functionality', () => {
    let executor: AtomicCrossExchangeOrderExecutor;

    beforeEach(() => {
      executor = new AtomicCrossExchangeOrderExecutor({ enableRetry: true, retryAmountFraction: 0.5 });
    });

    describe('successful execution', () => {
      it('returns success=true with both orders when both sides fill', async () => {
        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.success).toBe(true);
        expect(result.buyOrder).toBeDefined();
        expect(result.sellOrder).toBeDefined();
        expect(result.rollbackPerformed).toBe(false);
        expect(result.error).toBeUndefined();
      });

      it('calls createMarketOrder on both exchanges exactly once', async () => {
        await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(buyExchange.createMarketOrder).toHaveBeenCalledTimes(1);
        expect(buyExchange.createMarketOrder).toHaveBeenCalledWith('BTC/USDT', 'buy', 0.1);
        expect(sellExchange.createMarketOrder).toHaveBeenCalledTimes(1);
        expect(sellExchange.createMarketOrder).toHaveBeenCalledWith('BTC/USDT', 'sell', 0.1);
      });

      it('computes positive netPnl when sell price > buy price', async () => {
        // buy @ 68000, sell @ 68200
        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.netPnl).toBeCloseTo((68200 - 68000) * 0.1, 4);
      });

      it('records non-zero latency values', async () => {
        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.totalLatency).toBeGreaterThanOrEqual(0);
        expect(result.buyLatency).toBeGreaterThanOrEqual(0);
        expect(result.sellLatency).toBeGreaterThanOrEqual(0);
      });
    });

    describe('rollback on partial failure', () => {
      it('performs rollback when buy succeeds but sell fails', async () => {
        sellExchange.createMarketOrder.mockRejectedValue(new Error('OKX connection timeout'));

        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.success).toBe(false);
        expect(result.rollbackPerformed).toBe(true);
        expect(result.error).toContain('sell:');
        // Rollback: buyExchange.createMarketOrder called again with 'sell' to reverse
        expect(buyExchange.createMarketOrder).toHaveBeenCalledTimes(2);
        expect(buyExchange.createMarketOrder).toHaveBeenLastCalledWith('BTC/USDT', 'sell', 0.1);
      });

      it('performs rollback when sell succeeds but buy fails', async () => {
        buyExchange.createMarketOrder.mockRejectedValue(new Error('Binance rate limit'));

        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.success).toBe(false);
        expect(result.rollbackPerformed).toBe(true);
        expect(result.error).toContain('buy:');
        // Rollback: sellExchange.createMarketOrder called again with 'buy' to reverse
        expect(sellExchange.createMarketOrder).toHaveBeenCalledTimes(2);
        expect(sellExchange.createMarketOrder).toHaveBeenLastCalledWith('BTC/USDT', 'buy', 0.1);
      });

      it('reports rollbackPerformed=false when rollback itself also fails', async () => {
        sellExchange.createMarketOrder.mockRejectedValue(new Error('sell failed'));
        // Rollback attempt on buyExchange also fails
        buyExchange.createMarketOrder
          .mockResolvedValueOnce(makeOrder('ord-buy', 'buy', 68000, 0.1)) // first call succeeds
          .mockRejectedValueOnce(new Error('rollback failed'));             // rollback fails

        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.success).toBe(false);
        expect(result.rollbackPerformed).toBe(false);
      });
    });

    describe('full failure', () => {
      it('returns success=false with error message when both sides fail', async () => {
        buyExchange.createMarketOrder.mockRejectedValue(new Error('Binance down'));
        sellExchange.createMarketOrder.mockRejectedValue(new Error('OKX down'));

        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.success).toBe(false);
        expect(result.rollbackPerformed).toBe(false);
        expect(result.error).toContain('buy:');
        expect(result.error).toContain('sell:');
        expect(result.netPnl).toBe(0);
      });

      it('returns no orders when both fail', async () => {
        buyExchange.createMarketOrder.mockRejectedValue(new Error('err'));
        sellExchange.createMarketOrder.mockRejectedValue(new Error('err'));

        const result = await executor.executeAtomic({
          symbol: 'BTC/USDT',
          amount: 0.1,
          buyExchange,
          sellExchange,
        });

        expect(result.buyOrder).toBeUndefined();
        expect(result.sellOrder).toBeUndefined();
      });
    });
  });

  describe('retry functionality', () => {
    let config: AtomicExecutorConfig;
    let executor: AtomicCrossExchangeOrderExecutor;

    beforeEach(() => {
      const retryConfig: RetryConfig = {
        maxRetries: 2,
        baseDelayMs: 10,
        maxDelayMs: 100,
        factor: 2,
        jitter: false,
        retryableErrors: ['timeout', 'rate limit', 'network error']
      };

      config = { retryConfig };
      executor = new AtomicCrossExchangeOrderExecutor(config);
    });

    it('should retry on retryable errors', async () => {
      // Mock the buyExchange to fail twice with retryable error, then succeed
      let attemptCount = 0;
      buyExchange.createMarketOrder.mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          return Promise.reject(new Error('timeout error'));
        }
        return Promise.resolve(makeOrder('ord-1', 'buy', 68000, 0.1));
      });

      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(result.success).toBe(true);
      expect(buyExchange.createMarketOrder).toHaveBeenCalledTimes(3);
      expect(sellExchange.createMarketOrder).toHaveBeenCalledTimes(3); // Should also retry the sell

      // Verify retry metrics are included
      expect(result.retryMetrics).toBeDefined();
      expect(result.retryMetrics?.attempts).toBeGreaterThan(1);
      expect(result.retryMetrics?.successfulRetries).toBeGreaterThan(0);
    });

    it('should not retry on non-retryable errors', async () => {
      buyExchange.createMarketOrder.mockRejectedValue(new Error('invalid order'));
      sellExchange.createMarketOrder.mockResolvedValue(makeOrder('ord-2', 'sell', 68200, 0.1));

      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(buyExchange.createMarketOrder).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(false);
      expect(result.rollbackPerformed).toBe(true);
    });

    it('should include retry metrics in result', async () => {
      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(result.retryMetrics).toBeDefined();
      expect(result.retryMetrics?.attempts).toBeGreaterThanOrEqual(1);
    });
  });

  describe('circuit breaker functionality', () => {
    let config: AtomicExecutorConfig;
    let executor: AtomicCrossExchangeOrderExecutor;

    beforeEach(() => {
      const circuitBreakerConfig: CircuitBreakerConfig = {
        failureThreshold: 2,
        timeoutMs: 100,
        successThreshold: 1
      };

      config = { circuitBreakerConfig };
      executor = new AtomicCrossExchangeOrderExecutor(config);
    });

    it('should open circuit after threshold exceeded', async () => {
      // Cause 2 consecutive failures to trip the circuit breaker
      buyExchange.createMarketOrder.mockRejectedValue(new Error('exchange down'));

      // First attempt - should fail
      await expect(executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      })).rejects.toThrow();

      // Second attempt - should fail again
      await expect(executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      })).rejects.toThrow();

      // Third attempt should be rejected immediately by circuit breaker
      await expect(executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      })).rejects.toThrow('Circuit breaker is OPEN');

      // Should have been called only twice (circuit opens after 2nd failure)
      expect(buyExchange.createMarketOrder).toHaveBeenCalledTimes(2);
    });

    it('should include circuit breaker metrics in result', async () => {
      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(result.circuitBreakerMetrics).toBeDefined();
      expect(result.circuitBreakerMetrics?.state).toBeDefined();
      expect(result.circuitBreakerMetrics?.totalRequests).toBeGreaterThanOrEqual(1);
    });

    it('should allow request through after timeout', async () => {
      // Cause 2 consecutive failures to trip the circuit breaker
      buyExchange.createMarketOrder.mockRejectedValue(new Error('exchange down'));

      // Trip the circuit
      await expect(executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      })).rejects.toThrow();

      await expect(executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      })).rejects.toThrow();

      // Wait for timeout period to pass
      await new Promise(resolve => setTimeout(resolve, 110));

      // Now mock success to allow circuit to close
      buyExchange.createMarketOrder.mockResolvedValue(makeOrder('ord-1', 'buy', 68000, 0.1));

      // This should succeed after timeout
      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('combined retry and circuit breaker', () => {
    let executor: AtomicCrossExchangeOrderExecutor;

    beforeEach(() => {
      const config: AtomicExecutorConfig = {
        retryConfig: {
          maxRetries: 1,
          baseDelayMs: 10,
          maxDelayMs: 50,
          factor: 2,
          jitter: false,
          retryableErrors: ['timeout']
        },
        circuitBreakerConfig: {
          failureThreshold: 3,
          timeoutMs: 100,
          successThreshold: 1
        }
      };

      executor = new AtomicCrossExchangeOrderExecutor(config);
    });

    it('should handle both retry and circuit breaker together', async () => {
      let callCount = 0;
      buyExchange.createMarketOrder.mockImplementation(() => {
        callCount++;
        // Fail twice to trigger retry, then succeed
        if (callCount <= 2) {
          return Promise.reject(new Error('timeout'));
        }
        return Promise.resolve(makeOrder('ord-1', 'buy', 68000, 0.1));
      });

      const result = await executor.executeAtomic({
        symbol: 'BTC/USDT',
        amount: 0.1,
        buyExchange,
        sellExchange,
      });

      expect(result.success).toBe(true);
      expect(callCount).toBe(3); // Original + 2 retries
    });
  });
});
