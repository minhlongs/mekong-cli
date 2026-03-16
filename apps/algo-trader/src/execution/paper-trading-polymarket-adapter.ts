/**
 * Paper Trading Polymarket Adapter — mirrors PolymarketAdapter interface
 * but places NO real orders. Logs all trades to paper-trades.json.
 * Toggle via PAPER_MODE=true env var.
 */

import { EventEmitter } from 'events';
import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../utils/logger';
import type { PolymarketOrder, PolymarketTick } from './polymarket-adapter';

export interface PaperTrade {
  id: string;
  timestamp: number;
  tokenId: string;
  marketId: string;
  side: 'BUY' | 'SELL';
  price: number;
  size: number;
  notional: number;
  type: 'limit' | 'market';
}

export interface PaperPnL {
  totalPnl: number;
  realizedPnl: number;
  unrealizedPnl: number;
  tradeCount: number;
  winCount: number;
  lossCount: number;
}

const PAPER_TRADES_PATH = path.resolve(process.cwd(), 'data', 'paper-trades.json');

export class PaperTradingPolymarketAdapter extends EventEmitter {
  private trades: PaperTrade[] = [];
  private positions = new Map<string, { size: number; avgPrice: number; side: 'BUY' | 'SELL' }>();
  private latestTicks = new Map<string, PolymarketTick>();
  private orderCounter = 0;
  private realizedPnl = 0;

  constructor() {
    super();
    this.loadTrades();
  }

  /** Connect — no-op for paper mode, just emit event */
  async connect(): Promise<void> {
    logger.info('[PaperTrading] Paper mode active — no real orders will be placed');
    this.emit('connect', { exchange: 'polymarket-paper' });
  }

  async disconnect(): Promise<void> {
    this.saveTrades();
    this.emit('disconnect', { exchange: 'polymarket-paper' });
  }

  /** Place paper limit order — logs trade, updates position, emits events */
  async placeLimitOrder(
    tokenId: string,
    price: number,
    size: number,
    side: 'BUY' | 'SELL',
  ): Promise<PolymarketOrder> {
    // Validate
    if (price <= 0 || price >= 1) throw new Error(`Invalid price ${price}`);
    if (size <= 0 || isNaN(size)) throw new Error(`Invalid size ${size}`);

    const trade = this.recordTrade(tokenId, price, size, side, 'limit');
    this.updatePosition(tokenId, price, size, side);

    const order: PolymarketOrder = {
      orderId: trade.id,
      tokenId,
      side,
      price,
      size,
      status: 'matched', // Paper orders fill instantly
      createdAt: Date.now(),
    };

    logger.info(`[PaperTrading] ${side} ${size}@${price.toFixed(4)} ${tokenId} (paper)`);
    this.emit('order:placed', order);
    return order;
  }

  /** Place paper market order */
  async placeMarketOrder(
    tokenId: string,
    amount: number,
    side: 'BUY' | 'SELL',
  ): Promise<PolymarketOrder> {
    const tick = this.latestTicks.get(tokenId);
    const fillPrice = tick ? (side === 'BUY' ? tick.ask : tick.bid) : 0.5;

    return this.placeLimitOrder(tokenId, fillPrice, amount, side);
  }

  /** Cancel — no-op for paper */
  async cancelOrder(_orderId: string): Promise<void> {
    logger.debug('[PaperTrading] Cancel (no-op in paper mode)');
  }

  async cancelAllOrders(): Promise<void> {
    logger.debug('[PaperTrading] Cancel all (no-op in paper mode)');
  }

  /** Feed real-time tick data for PnL calculations */
  updateTick(tick: PolymarketTick): void {
    this.latestTicks.set(tick.tokenId, tick);
  }

  /** Get paper PnL summary */
  getPnL(): PaperPnL {
    let unrealizedPnl = 0;
    for (const [tokenId, pos] of this.positions) {
      const tick = this.latestTicks.get(tokenId);
      if (!tick) continue;
      const currentPrice = pos.side === 'BUY' ? tick.bid : tick.ask;
      const pnl = pos.side === 'BUY'
        ? (currentPrice - pos.avgPrice) * pos.size
        : (pos.avgPrice - currentPrice) * pos.size;
      unrealizedPnl += pnl;
    }

    const wins = this.trades.filter((_, i) => {
      // Simple: compare consecutive BUY→SELL pairs
      return false; // Simplified — use realized PnL instead
    });

    return {
      totalPnl: this.realizedPnl + unrealizedPnl,
      realizedPnl: this.realizedPnl,
      unrealizedPnl,
      tradeCount: this.trades.length,
      winCount: 0, // Tracked via realizedPnl sign
      lossCount: 0,
    };
  }

  /** Get all paper trades */
  getTrades(): PaperTrade[] {
    return [...this.trades];
  }

  /** Get open positions */
  getPositions(): Map<string, { size: number; avgPrice: number; side: 'BUY' | 'SELL' }> {
    return new Map(this.positions);
  }

  isConnected(): boolean { return true; }
  getActiveOrdersCount(): number { return 0; }

  // --- Private ---

  private recordTrade(tokenId: string, price: number, size: number, side: 'BUY' | 'SELL', type: 'limit' | 'market'): PaperTrade {
    const trade: PaperTrade = {
      id: `paper_${++this.orderCounter}_${Date.now()}`,
      timestamp: Date.now(),
      tokenId,
      marketId: tokenId, // Polymarket tokenId maps to market
      side,
      price,
      size,
      notional: price * size,
      type,
    };
    this.trades.push(trade);
    this.saveTrades();
    return trade;
  }

  private updatePosition(tokenId: string, price: number, size: number, side: 'BUY' | 'SELL'): void {
    const existing = this.positions.get(tokenId);

    if (!existing) {
      this.positions.set(tokenId, { size, avgPrice: price, side });
      return;
    }

    if (existing.side === side) {
      // Add to position — weighted average price
      const totalSize = existing.size + size;
      existing.avgPrice = (existing.avgPrice * existing.size + price * size) / totalSize;
      existing.size = totalSize;
    } else {
      // Closing position — realize PnL
      const closeSize = Math.min(existing.size, size);
      const pnl = existing.side === 'BUY'
        ? (price - existing.avgPrice) * closeSize
        : (existing.avgPrice - price) * closeSize;
      this.realizedPnl += pnl;

      existing.size -= closeSize;
      if (existing.size <= 0.001) {
        this.positions.delete(tokenId);
      }
    }
  }

  private saveTrades(): void {
    try {
      const dir = path.dirname(PAPER_TRADES_PATH);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      // Keep last 1000 trades
      const toSave = this.trades.slice(-1000);
      fs.writeFileSync(PAPER_TRADES_PATH, JSON.stringify(toSave, null, 2));
    } catch (err) {
      logger.warn('[PaperTrading] Failed to save trades:', err instanceof Error ? err.message : String(err));
    }
  }

  private loadTrades(): void {
    try {
      if (fs.existsSync(PAPER_TRADES_PATH)) {
        this.trades = JSON.parse(fs.readFileSync(PAPER_TRADES_PATH, 'utf8'));
        this.orderCounter = this.trades.length;
        logger.info(`[PaperTrading] Loaded ${this.trades.length} historical paper trades`);
      }
    } catch {
      this.trades = [];
    }
  }
}
