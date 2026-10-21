/**
 * LatencyOptimizer types and default configuration.
 */

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

export const DEFAULT_LATENCY_OPTIMIZER_CONFIG: LatencyOptimizerConfig = {
  historySize: 100,
  warmupIntervalMs: 10000,
  maxAcceptableMs: 500,
  targetExecutionMs: 100,
};
