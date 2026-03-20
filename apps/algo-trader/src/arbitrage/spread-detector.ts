/**
 * Spread Detector
 * Detects arbitrage opportunities across exchanges
 *
 * Algorithm:
 * - For each symbol: find best bid (exchange A) vs best ask (exchange B)
 * - Calculate spread: (best_bid - best_ask) / best_ask * 100
 * - Filter: spread > threshold (default 0.1%)
 */

import { getRedisClient } from '../redis';

export interface ArbitrageOpportunity {
  id: string;
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  spread: number;
  spreadPercent: number;
  timestamp: number;
  latency: number;
}

export interface SpreadConfig {
  minSpreadPercent: number;
  maxLatencyMs: number;
  checkIntervalMs: number;
}

export class SpreadDetector {
  private redis: ReturnType<typeof getRedisClient>;
  private config: SpreadConfig;
  private running = false;
  private intervalId: NodeJS.Timeout | null = null;

  constructor(config?: Partial<SpreadConfig>) {
    this.redis = getRedisClient();
    this.config = {
      minSpreadPercent: 0.1,
      maxLatencyMs: 500,
      checkIntervalMs: 100,
      ...config,
    };
  }

  private getTickerKey(exchange: string, symbol: string): string {
    return `ticker:${exchange}:${symbol}`;
  }

  /**
   * Get best bid/ask across all exchanges for a symbol
   */
  async getBestPrices(symbol: string, exchanges: string[]): Promise<{
    bestBid: { exchange: string; price: number } | null;
    bestAsk: { exchange: string; price: number } | null;
  }> {
    let bestBid: { exchange: string; price: number } | null = null;
    let bestAsk: { exchange: string; price: number } | null = null;

    for (const exchange of exchanges) {
      const key = this.getTickerKey(exchange, symbol);
      const ticker = await this.redis.hgetall(key);

      if (!ticker || Object.keys(ticker).length === 0) continue;

      const bid = parseFloat(ticker.bid) || 0;
      const ask = parseFloat(ticker.ask) || 0;

      if (bid > 0 && (!bestBid || bid > bestBid.price)) {
        bestBid = { exchange, price: bid };
      }
      if (ask > 0 && (!bestAsk || ask < bestAsk.price)) {
        bestAsk = { exchange, price: ask };
      }
    }

    return { bestBid, bestAsk };
  }

  /**
   * Calculate spread for a symbol across exchanges
   */
  async calculateSpread(
    symbol: string,
    exchanges: string[]
  ): Promise<ArbitrageOpportunity | null> {
    const { bestBid, bestAsk } = await this.getBestPrices(symbol, exchanges);

    if (!bestBid || !bestAsk) return null;

    const spread = bestBid.price - bestAsk.price;
    const spreadPercent = (spread / bestAsk.price) * 100;

    if (spreadPercent <= this.config.minSpreadPercent) return null;

    return {
      id: `arb-${symbol}-${Date.now()}`,
      symbol,
      buyExchange: bestAsk.exchange,
      sellExchange: bestBid.exchange,
      buyPrice: bestAsk.price,
      sellPrice: bestBid.price,
      spread,
      spreadPercent,
      timestamp: Date.now(),
      latency: 0,
    };
  }

  /**
   * Scan all symbols for arbitrage opportunities
   */
  async scan(
    symbols: string[],
    exchanges: string[]
  ): Promise<ArbitrageOpportunity[]> {
    const opportunities: ArbitrageOpportunity[] = [];

    for (const symbol of symbols) {
      const opp = await this.calculateSpread(symbol, exchanges);
      if (opp) {
        opportunities.push(opp);
      }
    }

    return opportunities;
  }

  /**
   * Start continuous spread detection
   */
  start(
    symbols: string[],
    exchanges: string[],
    onOpportunity: (opps: ArbitrageOpportunity[]) => void
  ): void {
    if (this.running) return;

    this.running = true;
    this.intervalId = setInterval(async () => {
      try {
        const opportunities = await this.scan(symbols, exchanges);
        if (opportunities.length > 0) {
          onOpportunity(opportunities);
        }
      } catch (error) {
        console.error('SpreadDetector scan error:', error);
      }
    }, this.config.checkIntervalMs);
  }

  /**
   * Stop spread detection
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.running = false;
  }

  /**
   * Store opportunity to Redis for execution module
   */
  async storeOpportunity(opp: ArbitrageOpportunity): Promise<void> {
    const key = `arbitrage:opportunities:${opp.id}`;
    const data = {
      ...opp,
      buyPrice: opp.buyPrice.toString(),
      sellPrice: opp.sellPrice.toString(),
      spread: opp.spread.toString(),
      spreadPercent: opp.spreadPercent.toString(),
    };

    const pipeline = this.redis.pipeline();
    pipeline.hset(key, data);
    pipeline.expire(key, 60); // 1 minute TTL
    await pipeline.exec();
  }

  /**
   * Get recent opportunities
   */
  async getRecentOpportunities(count = 100): Promise<ArbitrageOpportunity[]> {
    const keys = await this.redis.keys('arbitrage:opportunities:*');
    const opportunities: ArbitrageOpportunity[] = [];

    for (const key of keys.slice(0, count)) {
      const data = await this.redis.hgetall(key);
      if (data && Object.keys(data).length > 0) {
        opportunities.push({
          id: data.id || '',
          symbol: data.symbol || '',
          buyExchange: data.buyExchange || '',
          sellExchange: data.sellExchange || '',
          buyPrice: parseFloat(data.buyPrice) || 0,
          sellPrice: parseFloat(data.sellPrice) || 0,
          spread: parseFloat(data.spread) || 0,
          spreadPercent: parseFloat(data.spreadPercent) || 0,
          timestamp: parseInt(data.timestamp) || 0,
          latency: parseInt(data.latency) || 0,
        });
      }
    }

    return opportunities.sort((a, b) => b.timestamp - a.timestamp);
  }
}
