/**
 * SpreadDetectorEngine types and default configuration.
 */

import { IExchange } from '@mekong/trading-core/interfaces';
import {
  ArbitrageOpportunity, ScannerConfig, ExecutorConfig,
  ExecutionResult, ExchangeConfig,
} from './arbitrage-types';
import { ScorerConfig, ScoredSignal } from './signal-scorer';
import { CircuitBreakerConfig, CircuitState } from './emergency-circuit-breaker';
import { SpreadHistoryConfig, SpreadZScore } from './spread-history-tracker';

export const TARGET_EXCHANGES = ['binance', 'okx', 'bybit'] as const;
export type TargetExchange = typeof TARGET_EXCHANGES[number];

export interface SpreadDetectorConfig {
  exchanges: ExchangeConfig[];
  symbols: string[];
  scanner: Partial<ScannerConfig>;
  executor: Partial<ExecutorConfig>;
  scorer: Partial<ScorerConfig>;
  circuitBreaker: Partial<CircuitBreakerConfig>;
  spreadHistory: Partial<SpreadHistoryConfig>;
  initialEquity: number;
  maxOpportunitiesPerCycle: number;
  enableOrderBookValidation: boolean;
  enableSignalScoring: boolean;
  enableSpreadHistory: boolean;
  logIntervalMs: number;
  orderbookRefreshMs: number;
  /** Optional: provide IExchange factory for creating clients from ExchangeConfig */
  exchangeFactory?: (config: ExchangeConfig) => IExchange;
}

export interface DetectionEvent {
  opportunity: ArbitrageOpportunity;
  signal: ScoredSignal | null;
  zScore: SpreadZScore | null;
  orderbookFeasible: boolean;
  executed: boolean;
  result: ExecutionResult | null;
  reason: string;
  timestamp: number;
}

export interface EngineStats {
  status: 'idle' | 'running' | 'stopped' | 'halted';
  uptime: number;
  totalDetections: number;
  totalScored: number;
  totalExecuted: number;
  successfulExecutions: number;
  skippedByScorer: number;
  skippedByOrderbook: number;
  skippedByCircuitBreaker: number;
  circuitState: CircuitState;
  connectedExchanges: string[];
  avgDetectionLatencyMs: number;
}

export const DEFAULT_SPREAD_DETECTOR_CONFIG: SpreadDetectorConfig = {
  exchanges: [],
  symbols: ['BTC/USDT', 'ETH/USDT'],
  scanner: { pollIntervalMs: 2000, minSpreadPercent: 0.05 },
  executor: { maxPositionSizeUsd: 1000, maxConcurrentTrades: 3 },
  scorer: { executeThreshold: 65 },
  circuitBreaker: { maxDailyLossUsd: 100, maxConsecutiveLosses: 5 },
  spreadHistory: { maxRecordsPerPair: 1000 },
  initialEquity: 10000,
  maxOpportunitiesPerCycle: 5,
  enableOrderBookValidation: true,
  enableSignalScoring: true,
  enableSpreadHistory: true,
  logIntervalMs: 60000,
  orderbookRefreshMs: 5000,
};
