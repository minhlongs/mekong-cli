/**
 * LatencyOptimizer — Sub-100ms execution routing for cross-exchange arbitrage.
 */

import { getArbLogger } from './arb-logger';
import {
  LatencyRecord, ExchangeLatencyProfile,
  LatencyOptimizerConfig, DEFAULT_LATENCY_OPTIMIZER_CONFIG,
} from './latency-optimizer-types';

export * from './latency-optimizer-types';

const logger = getArbLogger();

export class LatencyOptimizer {
  private config: LatencyOptimizerConfig;
  private history: Map<string, LatencyRecord[]> = new Map();
  private warmupTimer: NodeJS.Timeout | null = null;
  private warmupCallbacks: Map<string, () => Promise<void>> = new Map();

  constructor(config?: Partial<LatencyOptimizerConfig>) {
    this.config = { ...DEFAULT_LATENCY_OPTIMIZER_CONFIG, ...config };
  }

  record(exchange: string, latencyMs: number, operation: LatencyRecord['operation'], success: boolean): void {
    if (!this.history.has(exchange)) this.history.set(exchange, []);

    const records = this.history.get(exchange)!;
    records.push({ exchange, latencyMs, timestamp: Date.now(), operation, success });

    if (records.length > this.config.historySize) {
      records.splice(0, records.length - this.config.historySize);
    }
  }

  getProfile(exchange: string): ExchangeLatencyProfile {
    const records = this.history.get(exchange) || [];
    if (records.length === 0) {
      return {
        exchange, avgTickerMs: 0, avgOrderMs: 0, p50Ms: 0, p95Ms: 0, p99Ms: 0,
        sampleCount: 0, successRate: 0, lastUpdated: 0,
      };
    }

    const successRecords = records.filter(r => r.success);
    const tickerRecords = successRecords.filter(r => r.operation === 'ticker');
    const orderRecords = successRecords.filter(r => r.operation === 'order');
    const allLatencies = successRecords.map(r => r.latencyMs).sort((a, b) => a - b);

    return {
      exchange,
      avgTickerMs: this.avg(tickerRecords.map(r => r.latencyMs)),
      avgOrderMs: this.avg(orderRecords.map(r => r.latencyMs)),
      p50Ms: this.percentile(allLatencies, 50),
      p95Ms: this.percentile(allLatencies, 95),
      p99Ms: this.percentile(allLatencies, 99),
      sampleCount: records.length,
      successRate: records.length > 0 ? (successRecords.length / records.length) * 100 : 0,
      lastUpdated: records[records.length - 1].timestamp,
    };
  }

  rankBySpeed(exchanges: string[]): string[] {
    return [...exchanges].sort((a, b) => this.getProfile(a).p50Ms - this.getProfile(b).p50Ms);
  }

  selectFastestPair(buyExchange: string, sellExchange: string): { first: string; second: string; estimatedTotalMs: number } {
    const buyProfile = this.getProfile(buyExchange);
    const sellProfile = this.getProfile(sellExchange);

    const estimatedTotalMs = Math.max(
      buyProfile.avgOrderMs || this.config.targetExecutionMs,
      sellProfile.avgOrderMs || this.config.targetExecutionMs
    );

    const buySlower = buyProfile.avgOrderMs >= sellProfile.avgOrderMs;
    return {
      first: buySlower ? buyExchange : sellExchange,
      second: buySlower ? sellExchange : buyExchange,
      estimatedTotalMs,
    };
  }

  meetsTarget(exchange: string): boolean {
    const profile = this.getProfile(exchange);
    if (profile.sampleCount === 0) return true;
    return profile.p95Ms <= this.config.maxAcceptableMs;
  }

  registerWarmup(exchange: string, callback: () => Promise<void>): void {
    this.warmupCallbacks.set(exchange, callback);
  }

  startWarmup(): void {
    if (this.warmupTimer) return;
    this.warmupTimer = setInterval(() => this.runWarmup(), this.config.warmupIntervalMs);
    logger.info(`[LatencyOpt] Warmup started (every ${this.config.warmupIntervalMs}ms)`);
  }

  stopWarmup(): void {
    if (this.warmupTimer) {
      clearInterval(this.warmupTimer);
      this.warmupTimer = null;
    }
  }

  async runWarmup(): Promise<void> {
    const tasks = Array.from(this.warmupCallbacks.entries()).map(async ([exchange, callback]) => {
      const start = Date.now();
      try {
        await callback();
        this.record(exchange, Date.now() - start, 'ticker', true);
      } catch {
        this.record(exchange, Date.now() - start, 'ticker', false);
      }
    });
    await Promise.allSettled(tasks);
  }

  getSummary(): ExchangeLatencyProfile[] {
    return Array.from(this.history.keys()).map(e => this.getProfile(e));
  }

  canAchieveTarget(): boolean {
    const profiles = this.getSummary();
    if (profiles.length < 2) return false;
    const fast = profiles.filter(p => p.p50Ms > 0 && p.p50Ms <= this.config.targetExecutionMs);
    return fast.length >= 2;
  }

  reset(): void {
    this.history.clear();
    this.stopWarmup();
  }

  private avg(values: number[]): number {
    return values.length === 0 ? 0 : values.reduce((s, v) => s + v, 0) / values.length;
  }

  private percentile(sorted: number[], p: number): number {
    if (sorted.length === 0) return 0;
    const idx = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[Math.max(0, idx)];
  }
}
