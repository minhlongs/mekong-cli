/**
 * RealTimePriceAggregator — Multi-exchange price feed aggregation.
 * Polls prices from all exchanges simultaneously, computes VWAP,
 * detects staleness, and provides unified price view.
 *
 * Flow: pollAll() → aggregate per symbol → VWAP + best bid/ask → emit
 */

import { ExchangeClient } from '../execution/ExchangeClient';
import { logger } from '../utils/logger';

export interface PriceTick {
  exchange: string;
  symbol: string;
  price: number;
  timestamp: number;
  latencyMs: number;
}

export interface AggregatedPrice {
  symbol: string;
  vwap: number;                                // Volume-weighted average (simplified: equal weight)
  bestBid: { exchange: string; price: number }; // Lowest price (buy here)
  bestAsk: { exchange: string; price: number }; // Highest price (sell here)
  spread: number;                               // bestAsk - bestBid
  spreadPercent: number;                        // spread / bestBid * 100
  tickCount: number;                            // Number of exchanges reporting
  staleness: number;                            // Max age of any tick in ms
  ticks: PriceTick[];                           // Raw ticks from each exchange
  timestamp: number;
}

export interface AggregatorConfig {
  pollIntervalMs: number;      // Poll frequency (default: 1000)
  staleThresholdMs: number;    // Mark price stale after this (default: 5000)
  minExchanges: number;        // Min exchanges needed for valid aggregate (default: 2)
}

const DEFAULT_CONFIG: AggregatorConfig = {
  pollIntervalMs: 1000,
  staleThresholdMs: 5000,
  minExchanges: 2,
};

export class RealTimePriceAggregator {
  private config: AggregatorConfig;
  private exchanges: Map<string, ExchangeClient> = new Map();
  private symbols: string[] = [];
  private latestTicks: Map<string, Map<string, PriceTick>> = new Map(); // symbol → exchange → tick
  private latestAggregates: Map<string, AggregatedPrice> = new Map();   // symbol → aggregate
  private listeners: ((agg: AggregatedPrice) => void)[] = [];
  private pollTimer: NodeJS.Timeout | null = null;
  private isRunning = false;
  private totalPolls = 0;

  constructor(config?: Partial<AggregatorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Register exchange to poll */
  addExchange(name: string, client: ExchangeClient): void {
    this.exchanges.set(name, client);
  }

  /** Set symbols to track */
  setSymbols(symbols: string[]): void {
    this.symbols = [...symbols];
    for (const s of symbols) {
      if (!this.latestTicks.has(s)) {
        this.latestTicks.set(s, new Map());
      }
    }
  }

  /** Subscribe to aggregated price updates */
  onUpdate(callback: (agg: AggregatedPrice) => void): void {
    this.listeners.push(callback);
  }

  /** Start polling loop */
  start(): void {
    if (this.isRunning) return;
    if (this.exchanges.size < this.config.minExchanges) {
      throw new Error(`RealTimePriceAggregator requires at least ${this.config.minExchanges} exchanges`);
    }
    if (this.symbols.length === 0) {
      throw new Error('No symbols configured — call setSymbols() first');
    }

    this.isRunning = true;
    this.pollAll(); // First poll immediately
    this.pollTimer = setInterval(() => this.pollAll(), this.config.pollIntervalMs);
    logger.info(`[PriceAgg] Started: ${this.exchanges.size} exchanges, ${this.symbols.length} symbols, ${this.config.pollIntervalMs}ms interval`);
  }

  /** Stop polling */
  stop(): void {
    this.isRunning = false;
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    logger.info(`[PriceAgg] Stopped after ${this.totalPolls} polls`);
  }

  /**
   * Single poll: fetch all prices, aggregate, notify listeners.
   * Can be called manually for testing.
   */
  async pollAll(): Promise<AggregatedPrice[]> {
    this.totalPolls++;
    const results: AggregatedPrice[] = [];

    // Fetch all prices in parallel
    const fetchTasks: Promise<void>[] = [];
    for (const symbol of this.symbols) {
      for (const [name, client] of this.exchanges) {
        fetchTasks.push(this.fetchTick(name, client, symbol));
      }
    }
    await Promise.allSettled(fetchTasks);

    // Aggregate per symbol
    for (const symbol of this.symbols) {
      const ticks = this.latestTicks.get(symbol);
      if (!ticks || ticks.size < this.config.minExchanges) continue;

      const agg = this.aggregate(symbol, ticks);
      this.latestAggregates.set(symbol, agg);
      results.push(agg);

      // Notify listeners
      for (const listener of this.listeners) {
        listener(agg);
      }
    }

    return results;
  }

  /** Fetch a single price tick */
  private async fetchTick(exchange: string, client: ExchangeClient, symbol: string): Promise<void> {
    const start = Date.now();
    try {
      const price = await client.fetchTicker(symbol);
      const latencyMs = Date.now() - start;

      const symbolMap = this.latestTicks.get(symbol)!;
      symbolMap.set(exchange, {
        exchange,
        symbol,
        price,
        timestamp: Date.now(),
        latencyMs,
      });
    } catch (err) {
      logger.warn(`[PriceAgg] Fetch failed ${exchange}/${symbol}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  /** Aggregate ticks for a symbol into unified view */
  private aggregate(symbol: string, ticks: Map<string, PriceTick>): AggregatedPrice {
    const now = Date.now();
    const validTicks: PriceTick[] = [];

    // Filter out stale ticks
    for (const tick of ticks.values()) {
      if (now - tick.timestamp <= this.config.staleThresholdMs && tick.price > 0) {
        validTicks.push(tick);
      }
    }

    if (validTicks.length === 0) {
      return this.emptyAggregate(symbol);
    }

    // Sort by price
    const sorted = [...validTicks].sort((a, b) => a.price - b.price);
    const lowest = sorted[0];
    const highest = sorted[sorted.length - 1];

    // VWAP (simplified: equal weight since we don't have volume data)
    const vwap = validTicks.reduce((sum, t) => sum + t.price, 0) / validTicks.length;

    const spread = highest.price - lowest.price;
    const spreadPercent = lowest.price > 0 ? (spread / lowest.price) * 100 : 0;
    const maxAge = Math.max(...validTicks.map(t => now - t.timestamp));

    return {
      symbol,
      vwap,
      bestBid: { exchange: lowest.exchange, price: lowest.price },
      bestAsk: { exchange: highest.exchange, price: highest.price },
      spread,
      spreadPercent,
      tickCount: validTicks.length,
      staleness: maxAge,
      ticks: validTicks,
      timestamp: now,
    };
  }

  /** Create empty aggregate for symbols with no valid data */
  private emptyAggregate(symbol: string): AggregatedPrice {
    return {
      symbol,
      vwap: 0,
      bestBid: { exchange: '', price: 0 },
      bestAsk: { exchange: '', price: 0 },
      spread: 0,
      spreadPercent: 0,
      tickCount: 0,
      staleness: Infinity,
      ticks: [],
      timestamp: Date.now(),
    };
  }

  /** Get latest aggregated price for a symbol */
  getLatest(symbol: string): AggregatedPrice | undefined {
    return this.latestAggregates.get(symbol);
  }

  /** Get all latest aggregates */
  getAllLatest(): Map<string, AggregatedPrice> {
    return new Map(this.latestAggregates);
  }

  /** Get raw ticks for a symbol */
  getTicks(symbol: string): PriceTick[] {
    const ticks = this.latestTicks.get(symbol);
    return ticks ? Array.from(ticks.values()) : [];
  }

  /** Check if we have sufficient price data */
  hasMinimumData(symbol: string): boolean {
    const ticks = this.latestTicks.get(symbol);
    if (!ticks) return false;

    const now = Date.now();
    let validCount = 0;
    for (const tick of ticks.values()) {
      if (now - tick.timestamp <= this.config.staleThresholdMs && tick.price > 0) {
        validCount++;
      }
    }
    return validCount >= this.config.minExchanges;
  }

  /** Get total poll count */
  getTotalPolls(): number {
    return this.totalPolls;
  }
}
