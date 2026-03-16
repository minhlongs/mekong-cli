/**
 * Base Strategy for Polymarket binary prediction markets
 *
 * Extends standard IStrategy with Polymarket-specific functionality
 */

import { IStrategy, ISignal, SignalType } from '../../interfaces/ISignal';
import { ICandle } from '../../interfaces/ICandle';
import { IPolymarketSignal, PolymarketSignalType, IMarketTick } from '../../interfaces/IPolymarket';

/** Position entry for stop-loss tracking */
interface OpenPosition {
  tokenId: string;
  marketId: string;
  side: 'YES' | 'NO';
  entryPrice: number;
  size: number;
  entryTime: number;
}

export abstract class BasePolymarketStrategy implements IStrategy {
  abstract name: string;

  protected marketTicks = new Map<string, IMarketTick>(); // tokenId -> tick
  protected config: Record<string, unknown> = {};
  protected maxHistoryBuffer: number = 100;

  // Stop-loss framework — enforced for all Polymarket strategies
  protected openPositions = new Map<string, OpenPosition>(); // tokenId -> position
  protected maxLossPerTrade: number = 0.15; // 15% max loss per position (configurable)
  protected maxHoldTimeMs: number = 24 * 60 * 60 * 1000; // 24h max hold (configurable)

  // Convert standard SignalType to PolymarketSignalType
  protected toPolymarketSignal(
    type: SignalType,
    tokenId: string,
    marketId: string,
    side: 'YES' | 'NO',
    price: number,
    size: number,
    metadata: IPolymarketSignal['metadata'] = {},
  ): IPolymarketSignal {
    const action = type === SignalType.BUY ? 'BUY' : 'SELL';
    const pmType = type === SignalType.BUY
      ? (side === 'YES' ? PolymarketSignalType.BUY_YES : PolymarketSignalType.BUY_NO)
      : (side === 'YES' ? PolymarketSignalType.SELL_YES : PolymarketSignalType.SELL_NO);

    return {
      type: pmType,
      tokenId,
      marketId,
      side,
      action,
      price,
      size,
      timestamp: Date.now(),
      metadata,
    };
  }

  /**
   * Initialize with market data
   */
  async init(candles: ICandle[], config?: Record<string, unknown>): Promise<void> {
    // Only merge config if provided, preserve subclass defaults
    if (config) {
      this.config = { ...this.config, ...config };
    }
    // For Polymarket, we use market ticks instead of candles
    this.candles = candles;
  }

  /**
   * Update configuration at runtime
   */
  async updateConfig(config: Record<string, unknown>): Promise<void> {
    this.config = { ...this.config, ...config };
  }

  getConfig(): Record<string, unknown> {
    return this.config;
  }

  getConfigSchema(): Record<string, unknown> {
    return {};
  }

  /**
   * Process market tick data
   */
  protected onMarketTick(tick: IMarketTick): void {
    this.marketTicks.set(tick.tokenId, tick);
  }

  /**
   * Get current tick for a token
   */
  protected getTick(tokenId: string): IMarketTick | undefined {
    return this.marketTicks.get(tokenId);
  }

  /**
   * Process tick with automatic stop-loss checking.
   * Call this from bot engine instead of calling processTick directly.
   * Returns exit signals first (stop-loss), then strategy entry signal if any.
   */
  processTickSafe(tick: IMarketTick): IPolymarketSignal[] {
    this.onMarketTick(tick);

    const signals: IPolymarketSignal[] = [];

    // Check stop-loss on all open positions first
    const exitSignals = this.checkStopLoss();
    signals.push(...exitSignals);

    // Then run strategy-specific logic
    const entrySignal = this.generateSignal(tick.tokenId, tick.marketId, tick);
    if (entrySignal && entrySignal.action === 'BUY') {
      // Auto-track new positions for stop-loss monitoring
      this.trackPosition(tick.tokenId, tick.marketId, entrySignal.side, entrySignal.price, entrySignal.size);
      signals.push(entrySignal);
    } else if (entrySignal) {
      signals.push(entrySignal);
    }

    return signals;
  }

  /**
   * Calculate fair value - to be implemented by subclasses
   */
  abstract calculateFairValue(tokenId: string): Promise<number | null>;

  /**
   * Generate signal based on price vs fair value
   * Subclasses can override with additional params
   */
  protected generateSignal(_tokenId: string, _marketId: string, _tick?: IMarketTick): IPolymarketSignal | null {
    return null;
  }

  // Candle storage for compatibility
  protected candles: ICandle[] = [];

  /**
   * Track a new open position (call after BUY signal is generated)
   */
  protected trackPosition(tokenId: string, marketId: string, side: 'YES' | 'NO', entryPrice: number, size: number): void {
    this.openPositions.set(tokenId, { tokenId, marketId, side, entryPrice, size, entryTime: Date.now() });
  }

  /**
   * Check all open positions for stop-loss or time-based exit
   * Returns SELL signals for positions that should be closed
   */
  protected checkStopLoss(): IPolymarketSignal[] {
    const exitSignals: IPolymarketSignal[] = [];
    const now = Date.now();
    const maxLoss = (this.config.maxLossPerTrade as number) ?? this.maxLossPerTrade;
    const maxHold = (this.config.maxHoldTimeMs as number) ?? this.maxHoldTimeMs;

    for (const [tokenId, pos] of this.openPositions) {
      const tick = this.getTick(tokenId);
      if (!tick) continue;

      const currentPrice = pos.side === 'YES' ? tick.bestBid : tick.bestAsk;
      if (!currentPrice || currentPrice <= 0) continue;

      const pnlPct = (currentPrice - pos.entryPrice) / pos.entryPrice;
      const holdTime = now - pos.entryTime;

      // Stop-loss: exit if loss exceeds threshold
      if (pnlPct < -maxLoss) {
        exitSignals.push(this.toPolymarketSignal(
          SignalType.SELL, tokenId, pos.marketId, pos.side, currentPrice, pos.size,
          { reason: 'stop_loss', pnlPct: pnlPct.toFixed(4), entryPrice: pos.entryPrice },
        ));
        this.openPositions.delete(tokenId);
        continue;
      }

      // Time-based exit: close stale positions
      if (holdTime > maxHold) {
        exitSignals.push(this.toPolymarketSignal(
          SignalType.SELL, tokenId, pos.marketId, pos.side, currentPrice, pos.size,
          { reason: 'max_hold_time', holdMs: holdTime, entryPrice: pos.entryPrice },
        ));
        this.openPositions.delete(tokenId);
      }
    }

    return exitSignals;
  }

  /**
   * Remove position from tracking (call on fill confirmation)
   */
  protected closePosition(tokenId: string): void {
    this.openPositions.delete(tokenId);
  }

  abstract onCandle(candle: ICandle): Promise<ISignal | null>;
}
