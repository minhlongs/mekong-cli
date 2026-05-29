/**
 * RealTimePriceAggregator — Multi-exchange price feed aggregation.
 * Polls prices from all exchanges simultaneously, computes VWAP,
 * detects staleness, and provides unified price view.
 * Uses IExchange interface for exchange abstraction.
 */

import { IExchange } from '@mekong/trading-core/interfaces';
import { getArbLogger } from './arb-logger';

export interface PriceTick {
  exchange: string;
  symbol: string;
  price: number;
  timestamp: number;
  latencyMs: number;
}

export interface AggregatedPrice {
  symbol: string;
  vwap: number;
  bestBid: { exchange: string; price: number };
  bestAsk: { exchange: string; price: number };
  spread: number;
  spreadPercent: number;
  tickCount: number;
  staleness: number;
  ticks: PriceTick[];
  timestamp: number;
}

export interface AggregatorConfig {
  pollIntervalMs: number;
  staleThresholdMs: number;
  minExchanges: number;
}

const DEFAULT_CONFIG: AggregatorConfig = {
  pollIntervalMs: 1000,
  staleThresholdMs: 5000,
  minExchanges: 2,
};

export class RealTimePriceAggregator {
  private config: AggregatorConfig;
  private exchanges: Map<string, IExchange> = new Map();
  private symbols: string[] = [];
  private latestTicks: Map<string, Map<string, PriceTick>> = new Map();
  private latestAggregates: Map<string, AggregatedPrice> = new Map();
  private listeners: ((agg: AggregatedPrice) => void)[] = [];
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private isRunning = false;
  private totalPolls = 0;

  constructor(config?: Partial<AggregatorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  addExchange(name: string, client: IExchange): void {
    this.exchanges.set(name, client);
  }

  setSymbols(symbols: string[]): void {
    this.symbols = [...symbols];
    for (const s of symbols) {
      if (!this.latestTicks.has(s)) this.latestTicks.set(s, new Map());
    }
  }

  onUpdate(callback: (agg: AggregatedPrice) => void): void {
    this.listeners.push(callback);
  }

  start(): void {
    if (this.isRunning) return;
    if (this.exchanges.size < this.config.minExchanges) {
      throw new Error(`RealTimePriceAggregator requires at least ${this.config.minExchanges} exchanges`);
    }
    if (this.symbols.length === 0) {
      throw new Error('No symbols configured — call setSymbols() first');
    }
    this.isRunning = true;
    this.pollAll();
    this.pollTimer = setInterval(() => this.pollAll(), this.config.pollIntervalMs);
    getArbLogger().info(`[PriceAgg] Started: ${this.exchanges.size} exchanges, ${this.symbols.length} symbols, ${this.config.pollIntervalMs}ms interval`);
  }

  stop(): void {
    this.isRunning = false;
    if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; }
    getArbLogger().info(`[PriceAgg] Stopped after ${this.totalPolls} polls`);
  }

  async pollAll(): Promise<AggregatedPrice[]> {
    this.totalPolls++;
    const results: AggregatedPrice[] = [];
    const fetchTasks: Promise<void>[] = [];

    for (const symbol of this.symbols) {
      for (const [name, client] of this.exchanges) {
        fetchTasks.push(this.fetchTick(name, client, symbol));
      }
    }
    await Promise.allSettled(fetchTasks);

    for (const symbol of this.symbols) {
      const ticks = this.latestTicks.get(symbol);
      if (!ticks || ticks.size < this.config.minExchanges) continue;
      const agg = this.aggregate(symbol, ticks);
      this.latestAggregates.set(symbol, agg);
      results.push(agg);
      for (const listener of this.listeners) listener(agg);
    }
    return results;
  }

  private async fetchTick(exchange: string, client: IExchange, symbol: string): Promise<void> {
    const start = Date.now();
    try {
      const price = await client.fetchTicker(symbol);
      const latencyMs = Date.now() - start;
      this.latestTicks.get(symbol)!.set(exchange, { exchange, symbol, price, timestamp: Date.now(), latencyMs });
    } catch (err) {
      getArbLogger().warn(`[PriceAgg] Fetch failed ${exchange}/${symbol}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  private aggregate(symbol: string, ticks: Map<string, PriceTick>): AggregatedPrice {
    const now = Date.now();
    const validTicks: PriceTick[] = [];
    for (const tick of ticks.values()) {
      if (now - tick.timestamp <= this.config.staleThresholdMs && tick.price > 0) validTicks.push(tick);
    }
    if (validTicks.length === 0) return this.emptyAggregate(symbol);

    const sorted = [...validTicks].sort((a, b) => a.price - b.price);
    const lowest = sorted[0];
    const highest = sorted[sorted.length - 1];
    const vwap = validTicks.reduce((sum, t) => sum + t.price, 0) / validTicks.length;
    const spread = highest.price - lowest.price;
    const spreadPercent = lowest.price > 0 ? (spread / lowest.price) * 100 : 0;
    const maxAge = Math.max(...validTicks.map(t => now - t.timestamp));

    return {
      symbol, vwap,
      bestBid: { exchange: lowest.exchange, price: lowest.price },
      bestAsk: { exchange: highest.exchange, price: highest.price },
      spread, spreadPercent, tickCount: validTicks.length, staleness: maxAge, ticks: validTicks, timestamp: now,
    };
  }

  private emptyAggregate(symbol: string): AggregatedPrice {
    return {
      symbol, vwap: 0, bestBid: { exchange: '', price: 0 }, bestAsk: { exchange: '', price: 0 },
      spread: 0, spreadPercent: 0, tickCount: 0, staleness: Infinity, ticks: [], timestamp: Date.now(),
    };
  }

  getLatest(symbol: string): AggregatedPrice | undefined { return this.latestAggregates.get(symbol); }
  getAllLatest(): Map<string, AggregatedPrice> { return new Map(this.latestAggregates); }
  getTicks(symbol: string): PriceTick[] { const t = this.latestTicks.get(symbol); return t ? Array.from(t.values()) : []; }

  hasMinimumData(symbol: string): boolean {
    const ticks = this.latestTicks.get(symbol);
    if (!ticks) return false;
    const now = Date.now();
    let valid = 0;
    for (const tick of ticks.values()) {
      if (now - tick.timestamp <= this.config.staleThresholdMs && tick.price > 0) valid++;
    }
    return valid >= this.config.minExchanges;
  }

  getTotalPolls(): number { return this.totalPolls; }
}
