/**
 * ArbitrageScanner — Multi-exchange price aggregator + spread detector.
 * Polls N exchanges in parallel, detects cross-exchange arbitrage opportunities.
 * Uses IExchange interface for exchange abstraction.
 *
 * Flow: poll() → aggregatePrices() → detectSpreads() → emit opportunities
 */

import { IExchange } from '@agencyos/trading-core/interfaces';
import { getArbLogger } from './arb-logger';
import {
  ExchangePrice, ArbitrageOpportunity, ScannerConfig, ScannerStats,
} from './arbitrage-types';

const DEFAULT_SCANNER_CONFIG: ScannerConfig = {
  symbols: ['BTC/USDT', 'ETH/USDT'],
  pollIntervalMs: 2000,
  minSpreadPercent: 0.1,
  feeRatePerSide: 0.001,
  slippageBps: 5,
  positionSizeUsd: 1000,
  maxPriceAgeMs: 5000,
};

export class ArbitrageScanner {
  private config: ScannerConfig;
  private exchanges: Map<string, IExchange> = new Map();
  private prices: Map<string, Map<string, ExchangePrice>> = new Map();
  private listeners: ((opp: ArbitrageOpportunity) => void)[] = [];
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private isRunning = false;
  private stats: ScannerStats = {
    totalPolls: 0,
    opportunitiesFound: 0,
    avgLatencyMs: 0,
    lastPollTime: 0,
    pricesByExchange: new Map(),
  };

  constructor(config?: Partial<ScannerConfig>) {
    this.config = { ...DEFAULT_SCANNER_CONFIG, ...config };
  }

  /** Add an exchange to monitor. Call before start(). */
  addExchange(name: string, client: IExchange): void {
    this.exchanges.set(name, client);
  }

  /** Register listener for arbitrage opportunities. */
  onOpportunity(callback: (opp: ArbitrageOpportunity) => void): void {
    this.listeners.push(callback);
  }

  /** Start the scanner loop. */
  async start(): Promise<void> {
    if (this.exchanges.size < 2) {
      throw new Error('ArbitrageScanner requires at least 2 exchanges');
    }

    const log = getArbLogger();
    log.info(`[ArbScanner] Starting: ${this.exchanges.size} exchanges, ${this.config.symbols.length} pairs, interval ${this.config.pollIntervalMs}ms`);

    await Promise.all(
      Array.from(this.exchanges.entries()).map(async ([name, client]) => {
        try {
          await client.connect();
          log.info(`[ArbScanner] Connected: ${name}`);
        } catch (err) {
          log.error(`[ArbScanner] Failed to connect ${name}: ${err instanceof Error ? err.message : String(err)}`);
        }
      })
    );

    this.isRunning = true;
    this.poll();
    this.pollTimer = setInterval(() => this.poll(), this.config.pollIntervalMs);
  }

  /** Stop the scanner. */
  stop(): void {
    this.isRunning = false;
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    getArbLogger().info(`[ArbScanner] Stopped. Stats: ${this.stats.totalPolls} polls, ${this.stats.opportunitiesFound} opportunities`);
  }

  /** Single poll: fetch all prices → detect spreads. */
  async poll(): Promise<ArbitrageOpportunity[]> {
    if (!this.isRunning && this.pollTimer) return [];

    this.stats.totalPolls++;
    const opportunities: ArbitrageOpportunity[] = [];
    const fetchTasks: Promise<void>[] = [];

    for (const symbol of this.config.symbols) {
      if (!this.prices.has(symbol)) {
        this.prices.set(symbol, new Map());
      }
      for (const [exchangeName, client] of this.exchanges) {
        fetchTasks.push(this.fetchPrice(exchangeName, client, symbol));
      }
    }

    await Promise.allSettled(fetchTasks);

    for (const symbol of this.config.symbols) {
      const symbolPrices = this.prices.get(symbol);
      if (!symbolPrices || symbolPrices.size < 2) continue;
      const opps = this.detectSpreads(symbol, symbolPrices);
      opportunities.push(...opps);
    }

    this.stats.lastPollTime = Date.now();
    this.stats.pricesByExchange = new Map(this.prices);
    return opportunities;
  }

  private async fetchPrice(exchangeName: string, client: IExchange, symbol: string): Promise<void> {
    const startMs = Date.now();
    try {
      const price = await client.fetchTicker(symbol);
      const latencyMs = Date.now() - startMs;
      const symbolMap = this.prices.get(symbol)!;
      symbolMap.set(exchangeName, { exchange: exchangeName, symbol, price, timestamp: Date.now(), latencyMs });
      this.stats.avgLatencyMs = (this.stats.avgLatencyMs + latencyMs) / 2;
    } catch (err) {
      getArbLogger().warn(`[ArbScanner] Fetch failed ${exchangeName}/${symbol}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  private detectSpreads(symbol: string, prices: Map<string, ExchangePrice>): ArbitrageOpportunity[] {
    const opportunities: ArbitrageOpportunity[] = [];
    const now = Date.now();
    const entries = Array.from(prices.entries());

    for (let i = 0; i < entries.length; i++) {
      for (let j = i + 1; j < entries.length; j++) {
        const [nameA, priceA] = entries[i];
        const [nameB, priceB] = entries[j];

        if (now - priceA.timestamp > this.config.maxPriceAgeMs) continue;
        if (now - priceB.timestamp > this.config.maxPriceAgeMs) continue;
        if (priceA.price <= 0 || priceB.price <= 0) continue;

        const spreadPercent = Math.abs(priceA.price - priceB.price) / Math.min(priceA.price, priceB.price) * 100;
        if (spreadPercent < this.config.minSpreadPercent) continue;

        const buyExchange = priceA.price < priceB.price ? nameA : nameB;
        const sellExchange = priceA.price < priceB.price ? nameB : nameA;
        const buyPrice = Math.min(priceA.price, priceB.price);
        const sellPrice = Math.max(priceA.price, priceB.price);

        const totalFees = this.config.feeRatePerSide * 2 * 100;
        const slippageCost = (this.config.slippageBps / 10000) * 2 * 100;
        const netProfitPercent = spreadPercent - totalFees - slippageCost;

        if (netProfitPercent <= 0) continue;

        const positionUnits = this.config.positionSizeUsd / buyPrice;
        const estimatedProfitUsd = positionUnits * (sellPrice - buyPrice) - (this.config.positionSizeUsd * (totalFees + slippageCost) / 100);

        const opp: ArbitrageOpportunity = {
          symbol, buyExchange, sellExchange, buyPrice, sellPrice,
          spreadPercent, netProfitPercent, estimatedProfitUsd,
          timestamp: now,
          latency: {
            buy: (priceA.price < priceB.price ? priceA : priceB).latencyMs,
            sell: (priceA.price >= priceB.price ? priceA : priceB).latencyMs,
          },
        };

        opportunities.push(opp);
        this.stats.opportunitiesFound++;

        for (const listener of this.listeners) {
          listener(opp);
        }
      }
    }
    return opportunities;
  }

  getStats(): ScannerStats { return { ...this.stats }; }
  getPrices(): Map<string, Map<string, ExchangePrice>> { return new Map(this.prices); }
}
