/**
 * Arbitrage shared types — cross-exchange spread detection, scoring, execution.
 * Used by ArbitrageScanner, ArbitrageExecutor, SpreadDetectorEngine.
 */

import { IOrder } from '@mekong/trading-core/interfaces';

// --- Scanner types ---

export interface ExchangePrice {
  exchange: string;
  symbol: string;
  price: number;
  timestamp: number;
  latencyMs: number;
}

export interface ArbitrageOpportunity {
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  spreadPercent: number;
  netProfitPercent: number;
  estimatedProfitUsd: number;
  timestamp: number;
  latency: { buy: number; sell: number };
}

export interface ScannerConfig {
  symbols: string[];
  pollIntervalMs: number;
  minSpreadPercent: number;
  feeRatePerSide: number;
  slippageBps: number;
  positionSizeUsd: number;
  maxPriceAgeMs: number;
}

export interface ScannerStats {
  totalPolls: number;
  opportunitiesFound: number;
  avgLatencyMs: number;
  lastPollTime: number;
  pricesByExchange: Map<string, Map<string, ExchangePrice>>;
}

// --- Executor types ---

export interface ExecutionResult {
  opportunity: ArbitrageOpportunity;
  buyOrder: IOrder | null;
  sellOrder: IOrder | null;
  actualProfitUsd: number;
  totalFeesUsd: number;
  executionTimeMs: number;
  slippageBps: { buy: number; sell: number };
  success: boolean;
  error?: string;
}

export interface ArbitrageTradeLog {
  id: number;
  timestamp: number;
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  amount: number;
  grossProfitUsd: number;
  feesUsd: number;
  netProfitUsd: number;
  executionTimeMs: number;
}

export interface PnLDashboard {
  totalTrades: number;
  successfulTrades: number;
  failedTrades: number;
  totalProfitUsd: number;
  totalFeesUsd: number;
  netProfitUsd: number;
  avgExecutionMs: number;
  bestTradeUsd: number;
  worstTradeUsd: number;
  winRate: number;
  profitFactor: number;
  activePositionValue: number;
}

export interface ExecutorConfig {
  maxPositionSizeUsd: number;
  maxConcurrentTrades: number;
  maxSlippageBps: number;
  feeRatePerSide: number;
  minNetProfitUsd: number;
  maxDailyLossUsd: number;
  cooldownMs: number;
}

// --- Multi-exchange connector types ---

export interface ExchangeConfig {
  id: string;
  apiKey?: string;
  secret?: string;
  label?: string;
  enabled: boolean;
  testMode?: boolean;
}
