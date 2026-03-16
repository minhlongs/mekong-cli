/**
 * Polymarket BotEngine Integration Tests
 *
 * Tests real signal-processing logic: circuit breaker, daily loss limit,
 * position size checks, and order execution for BUY/SELL/CANCEL signals.
 */

import { PolymarketBotEngine, PolymarketBotConfig } from '../../src/polymarket/bot-engine';
import { IPolymarketSignal } from '../../src/interfaces/IPolymarket';
import { PolymarketSignalType } from '../../src/interfaces/IPolymarket';

// --- Mock heavy dependencies so no real exchange calls happen ---

jest.mock('../../src/execution/polymarket-adapter', () => {
  const mockAdapter = {
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn().mockResolvedValue(undefined),
    cancelAllOrders: jest.fn().mockResolvedValue(undefined),
    cancelOrder: jest.fn().mockResolvedValue(undefined),
    placeLimitOrder: jest.fn().mockResolvedValue({
      orderId: 'order-mock-1',
      tokenId: 'tok-1',
      marketId: 'mkt-1',
      side: 'YES',
      action: 'BUY',
      price: 0.55,
      size: 10,
      status: 'live',
      createdAt: Date.now(),
    }),
    getOrderBook: jest.fn().mockResolvedValue({ asks: [], bids: [] }),
    on: jest.fn(),
  };
  return { PolymarketAdapter: jest.fn(() => mockAdapter) };
});

jest.mock('../../src/utils/logger', () => ({
  logger: { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() },
}));

jest.mock('../../src/core/state-manager', () => ({
  saveState: jest.fn(),
  loadState: jest.fn().mockReturnValue(null),
}));

// Helper — build a minimal valid signal
function makeSignal(overrides: Partial<IPolymarketSignal> = {}): IPolymarketSignal {
  return {
    type: PolymarketSignalType.BUY_YES,
    tokenId: 'tok-1',
    marketId: 'mkt-1',
    side: 'YES',
    action: 'BUY',
    price: 0.55,
    size: 10,
    metadata: { strategy: 'TestStrategy' },
    ...overrides,
  };
}

// Helper — build engine in dry-run mode with tight risk limits
function makeEngine(cfg: Partial<PolymarketBotConfig> = {}): PolymarketBotEngine {
  return new PolymarketBotEngine({
    dryRun: true,
    maxBankroll: 1000,
    maxPositionPct: 0.10,   // max $100 per position
    maxDailyLoss: 0.05,     // max $50 daily loss
    minEdgeThreshold: 0.01,
    enabledStrategies: [],  // no auto-strategies — we'll inject signals manually
    ...cfg,
  });
}

// Expose private processSignal for unit testing via any-cast
function processSignal(engine: PolymarketBotEngine, signal: IPolymarketSignal): void {
  (engine as any).processSignal(signal);
}

// ---- Tests ----

describe('PolymarketBotEngine signal processing', () => {

  describe('circuit breaker guard', () => {
    it('rejects signal when circuit breaker is tripped', () => {
      const engine = makeEngine();
      // Trip the circuit breaker directly
      (engine as any).circuitBreaker.trip('test');

      const rejected: unknown[] = [];
      engine.on('signal:rejected', (e) => rejected.push(e));

      processSignal(engine, makeSignal());

      expect(rejected).toHaveLength(1);
      expect((rejected[0] as any).reason).toBe('circuit_breaker');
    });
  });

  describe('daily loss limit guard', () => {
    it('stops trading when daily loss limit is reached', () => {
      const engine = makeEngine();
      // Saturate daily loss: limit is 5% of $1000 = $50
      (engine as any).dailyLoss = 50;

      const rejected: unknown[] = [];
      engine.on('signal:rejected', (e) => rejected.push(e));

      processSignal(engine, makeSignal());

      expect(rejected).toHaveLength(1);
      expect((rejected[0] as any).reason).toBe('daily_loss_limit');
    });
  });

  describe('position size guard', () => {
    it('rejects signal when notional value exceeds max position', () => {
      const engine = makeEngine();
      // maxPosition = 10% * $1000 = $100; notional = price * size
      const oversized = makeSignal({ price: 0.9, size: 200 }); // notional = $180 > $100

      const rejected: unknown[] = [];
      engine.on('signal:rejected', (e) => rejected.push(e));

      processSignal(engine, oversized);

      expect(rejected).toHaveLength(1);
      expect((rejected[0] as any).reason).toBe('position_size');
    });

    it('passes signal through when size is within limit', () => {
      const engine = makeEngine();
      const okSignal = makeSignal({ price: 0.5, size: 10 }); // notional = $5, well under $100

      const rejected: unknown[] = [];
      engine.on('signal:rejected', (e) => rejected.push(e));
      engine.on('signal:executed', () => {}); // suppress unhandled

      processSignal(engine, okSignal);

      expect(rejected).toHaveLength(0);
    });
  });

  describe('BUY signal execution (dry-run)', () => {
    it('emits signal:executed with dryRun=true for a BUY signal', () => {
      const engine = makeEngine({ dryRun: true });
      const signal = makeSignal({ action: 'BUY', type: PolymarketSignalType.BUY_YES });

      const executed: unknown[] = [];
      engine.on('signal:executed', (e) => executed.push(e));

      processSignal(engine, signal);

      expect(executed).toHaveLength(1);
      expect((executed[0] as any).dryRun).toBe(true);
      expect((executed[0] as any).signal.action).toBe('BUY');
    });
  });

  describe('SELL signal execution (dry-run)', () => {
    it('emits signal:executed with dryRun=true for a SELL signal', () => {
      const engine = makeEngine({ dryRun: true });
      const signal = makeSignal({
        action: 'SELL',
        type: PolymarketSignalType.SELL_YES,
      });

      const executed: unknown[] = [];
      engine.on('signal:executed', (e) => executed.push(e));

      processSignal(engine, signal);

      expect(executed).toHaveLength(1);
      expect((executed[0] as any).dryRun).toBe(true);
      expect((executed[0] as any).signal.action).toBe('SELL');
    });
  });

  describe('CANCEL signal execution (dry-run)', () => {
    it('emits signal:executed with dryRun=true for a CANCEL signal', () => {
      const engine = makeEngine({ dryRun: true });
      const signal = makeSignal({
        action: 'CANCEL',
        type: PolymarketSignalType.NONE,
      });

      const executed: unknown[] = [];
      engine.on('signal:executed', (e) => executed.push(e));

      processSignal(engine, signal);

      expect(executed).toHaveLength(1);
      expect((executed[0] as any).dryRun).toBe(true);
      expect((executed[0] as any).signal.action).toBe('CANCEL');
    });
  });
});
