/**
 * SpreadHistoryTracker — Historical spread analysis for cross-exchange arbitrage.
 */

import {
  SpreadRecord, SpreadStats, SpreadZScore, HourlyPattern,
  SpreadHistoryConfig, DEFAULT_SPREAD_HISTORY_CONFIG,
} from './spread-history-types';

export * from './spread-history-types';

export class SpreadHistoryTracker {
  private config: SpreadHistoryConfig;
  private history: Map<string, SpreadRecord[]> = new Map();

  constructor(config?: Partial<SpreadHistoryConfig>) {
    this.config = { ...DEFAULT_SPREAD_HISTORY_CONFIG, ...config };
  }

  record(record: SpreadRecord): void {
    const key = this.pairKey(record.buyExchange, record.sellExchange, record.symbol);
    if (!this.history.has(key)) this.history.set(key, []);

    const records = this.history.get(key)!;
    records.push(record);

    if (records.length > this.config.maxRecordsPerPair) {
      records.splice(0, records.length - this.config.maxRecordsPerPair);
    }
  }

  getStats(buyExchange: string, sellExchange: string, symbol: string): SpreadStats {
    const key = this.pairKey(buyExchange, sellExchange, symbol);
    const records = this.history.get(key) || [];
    if (records.length === 0) return this.emptyStats(key, symbol, buyExchange, sellExchange);

    const spreads = records.map(r => r.spreadPercent);
    const sorted = [...spreads].sort((a, b) => a - b);
    const mean = this.mean(spreads);
    const stddev = this.stddev(spreads, mean);
    const last = records[records.length - 1];

    return {
      pairKey: key, symbol, buyExchange, sellExchange, mean, stddev,
      min: sorted[0], max: sorted[sorted.length - 1],
      median: sorted[Math.floor(sorted.length / 2)],
      count: records.length, lastSpread: last.spreadPercent, lastTimestamp: last.timestamp,
    };
  }

  getZScore(buyExchange: string, sellExchange: string, symbol: string, currentSpread: number): SpreadZScore {
    const stats = this.getStats(buyExchange, sellExchange, symbol);
    const zScore = stats.stddev > 0 ? (currentSpread - stats.mean) / stats.stddev : 0;

    return {
      pairKey: stats.pairKey, currentSpread, mean: stats.mean, stddev: stats.stddev,
      zScore, isAnomaly: zScore >= this.config.anomalyThreshold,
    };
  }

  getHourlyPatterns(buyExchange: string, sellExchange: string, symbol: string): HourlyPattern[] {
    const key = this.pairKey(buyExchange, sellExchange, symbol);
    const records = this.history.get(key) || [];
    const cutoff = Date.now() - this.config.patternWindowHours * 3600000;
    const recent = records.filter(r => r.timestamp >= cutoff);

    const hourBuckets: Map<number, number[]> = new Map();
    for (let h = 0; h < 24; h++) hourBuckets.set(h, []);

    for (const r of recent) {
      const hour = new Date(r.timestamp).getUTCHours();
      hourBuckets.get(hour)!.push(r.spreadPercent);
    }

    return Array.from(hourBuckets.entries()).map(([hour, spreads]) => ({
      hour,
      avgSpread: spreads.length > 0 ? this.mean(spreads) : 0,
      tradeCount: spreads.length,
      bestSpread: spreads.length > 0 ? Math.max(...spreads) : 0,
    }));
  }

  getBestTradingHours(buyExchange: string, sellExchange: string, symbol: string, topN: number = 5): HourlyPattern[] {
    return this.getHourlyPatterns(buyExchange, sellExchange, symbol)
      .filter(p => p.tradeCount > 0)
      .sort((a, b) => b.avgSpread - a.avgSpread)
      .slice(0, topN);
  }

  getTrackedPairs(): string[] { return Array.from(this.history.keys()); }

  getAllStats(): SpreadStats[] {
    return this.getTrackedPairs().map(key => {
      const records = this.history.get(key)!;
      if (records.length === 0) return null;
      const first = records[0];
      return this.getStats(first.buyExchange, first.sellExchange, first.symbol);
    }).filter((s): s is SpreadStats => s !== null);
  }

  getTotalRecords(): number {
    let total = 0;
    for (const records of this.history.values()) total += records.length;
    return total;
  }

  clear(): void { this.history.clear(); }

  private pairKey(buy: string, sell: string, symbol: string): string {
    return `${buy}→${sell}:${symbol}`;
  }

  private mean(values: number[]): number {
    return values.length === 0 ? 0 : values.reduce((s, v) => s + v, 0) / values.length;
  }

  private stddev(values: number[], mean: number): number {
    if (values.length < 2) return 0;
    return Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length);
  }

  private emptyStats(key: string, symbol: string, buy: string, sell: string): SpreadStats {
    return {
      pairKey: key, symbol, buyExchange: buy, sellExchange: sell,
      mean: 0, stddev: 0, min: 0, max: 0, median: 0, count: 0, lastSpread: 0, lastTimestamp: 0,
    };
  }
}
