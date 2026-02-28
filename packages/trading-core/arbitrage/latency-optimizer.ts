/**
 * LatencyOptimizer — Sub-100ms execution routing for cross-exchange arbitrage.
 * Tracks per-exchange latency history, selects fastest routes,
 * pre-warms connections, and provides latency-aware execution ordering.
 */

import { getArbLogger } from './arb-logger';
const logger = getArbLogger();

export interface LatencyRecord {
  exchange: string;
  latencyMs: number;
  timestamp: number;
  operation: 'ticker' | 'order' | 'balance';
  success: boolean;
}

export interface ExchangeLatencyProfile {
  exchange: string;
  avgTickerMs: number;
  avgOrderMs: number;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
  sampleCount: number;
  successRate: number;
  lastUpdated: number;
}

export interface LatencyOptimizerConfig {
  historySize: number;          // Max records per exchange (default: 100)
  warmupIntervalMs: number;     // Pre-warm interval (default: 10000)
  maxAcceptableMs: number;      // Max latency before marking exchange slow (default: 500)
  targetExecutionMs: number;    // Target total execution time (default: 100)
}

const DEFAULT_CONFIG: LatencyOptimizerConfig = {
  historySize: 100,
  warmupIntervalMs: 10000,
  maxAcceptableMs: 500,
  targetExecutionMs: 100,
};

export class LatencyOptimizer {
  private config: LatencyOptimizerConfig;
  private history: Map<string, LatencyRecord[]> = new Map(); // exchange → records
  private warmupTimer: NodeJS.Timeout | null = null;
  private warmupCallbacks: Map<string, () => Promise<void>> = new Map();

  constructor(config?: Partial<LatencyOptimizerConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Record a latency measurement for an exchange.
   */
  record(exchange: string, latencyMs: number, operation: LatencyRecord['operation'], success: boolean): void {
    if (!this.history.has(exchange)) {
      this.history.set(exchange, []);
    }

    const records = this.history.get(exchange)!;
    records.push({
      exchange,
      latencyMs,
      timestamp: Date.now(),
      operation,
      success,
    });

    // Trim to max history size
    if (records.length > this.config.historySize) {
      records.splice(0, records.length - this.config.historySize);
    }
  }

  /**
   * Get latency profile for an exchange.
   */
  getProfile(exchange: string): ExchangeLatencyProfile {
    const records = this.history.get(exchange) || [];
    if (records.length === 0) {
      return {
        exchange,
        avgTickerMs: 0,
        avgOrderMs: 0,
        p50Ms: 0,
        p95Ms: 0,
        p99Ms: 0,
        sampleCount: 0,
        successRate: 0,
        lastUpdated: 0,
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

  /**
   * Rank exchanges by latency (fastest first).
   * Used to determine optimal execution order.
   */
  rankBySpeed(exchanges: string[]): string[] {
    return [...exchanges].sort((a, b) => {
      const profileA = this.getProfile(a);
      const profileB = this.getProfile(b);
      // Sort by p50 latency — more stable than avg
      return profileA.p50Ms - profileB.p50Ms;
    });
  }

  /**
   * Select the fastest exchange pair for an arbitrage trade.
   * Returns [buyExchange, sellExchange] ordered for minimum total latency.
   */
  selectFastestPair(buyExchange: string, sellExchange: string): { first: string; second: string; estimatedTotalMs: number } {
    const buyProfile = this.getProfile(buyExchange);
    const sellProfile = this.getProfile(sellExchange);

    // Both execute in parallel, so total time = max(buy, sell)
    const estimatedTotalMs = Math.max(
      buyProfile.avgOrderMs || this.config.targetExecutionMs,
      sellProfile.avgOrderMs || this.config.targetExecutionMs
    );

    // Return slower exchange first (start it earlier if sequential fallback needed)
    const buySlower = buyProfile.avgOrderMs >= sellProfile.avgOrderMs;
    return {
      first: buySlower ? buyExchange : sellExchange,
      second: buySlower ? sellExchange : buyExchange,
      estimatedTotalMs,
    };
  }

  /**
   * Check if an exchange meets the target latency for execution.
   */
  meetsTarget(exchange: string): boolean {
    const profile = this.getProfile(exchange);
    if (profile.sampleCount === 0) return true; // No data yet, assume OK
    return profile.p95Ms <= this.config.maxAcceptableMs;
  }

  /**
   * Register a warmup callback for an exchange (e.g., ping ticker).
   */
  registerWarmup(exchange: string, callback: () => Promise<void>): void {
    this.warmupCallbacks.set(exchange, callback);
  }

  /**
   * Start pre-warming connections to keep them hot.
   */
  startWarmup(): void {
    if (this.warmupTimer) return;

    this.warmupTimer = setInterval(() => this.runWarmup(), this.config.warmupIntervalMs);
    logger.info(`[LatencyOpt] Warmup started (every ${this.config.warmupIntervalMs}ms)`);
  }

  /**
   * Stop warmup loop.
   */
  stopWarmup(): void {
    if (this.warmupTimer) {
      clearInterval(this.warmupTimer);
      this.warmupTimer = null;
    }
  }

  /**
   * Execute one warmup cycle.
   */
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

  /**
   * Get summary of all exchange latencies.
   */
  getSummary(): ExchangeLatencyProfile[] {
    const exchanges = Array.from(this.history.keys());
    return exchanges.map(e => this.getProfile(e));
  }

  /**
   * Check if overall system can achieve sub-100ms execution.
   */
  canAchieveTarget(): boolean {
    const profiles = this.getSummary();
    if (profiles.length < 2) return false;

    // Need at least 2 exchanges with acceptable latency
    const fast = profiles.filter(p => p.p50Ms > 0 && p.p50Ms <= this.config.targetExecutionMs);
    return fast.length >= 2;
  }

  /** Clear all history */
  reset(): void {
    this.history.clear();
    this.stopWarmup();
  }

  private avg(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((s, v) => s + v, 0) / values.length;
  }

  private percentile(sorted: number[], p: number): number {
    if (sorted.length === 0) return 0;
    const idx = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[Math.max(0, idx)];
  }
}
