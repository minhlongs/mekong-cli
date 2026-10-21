/**
 * ArbitrageOrchestrator types and default configuration.
 */

import { ExchangeConfig, ScannerConfig, ExecutorConfig } from './arbitrage-types';
import { ExchangeFactory } from './multi-exchange-connector';

export interface OrchestratorConfig {
  exchanges: ExchangeConfig[];
  symbols: string[];
  scanner: Partial<ScannerConfig>;
  executor: Partial<ExecutorConfig>;
  enableLatencyOptimizer: boolean;
  enableProfitTracker: boolean;
  enableAdaptiveThreshold: boolean;
  enableWebSocket: boolean;
  initialEquity: number;
  maxDrawdownPercent: number;
  dailyResetHourUtc: number;
  maxOpportunitiesPerCycle: number;
  logIntervalMs: number;
  /** Factory to create IExchange from ExchangeConfig */
  exchangeFactory?: ExchangeFactory;
}

export interface OrchestratorStats {
  status: 'idle' | 'running' | 'stopped';
  uptime: number;
  totalCycles: number;
  totalOpportunities: number;
  totalExecutions: number;
  successfulExecutions: number;
  connectedExchanges: number;
  lastCycleMs: number;
}

export const DEFAULT_ORCHESTRATOR_CONFIG: OrchestratorConfig = {
  exchanges: [],
  symbols: ['BTC/USDT', 'ETH/USDT'],
  scanner: {},
  executor: {},
  enableLatencyOptimizer: true,
  enableProfitTracker: true,
  enableAdaptiveThreshold: true,
  enableWebSocket: false,
  initialEquity: 10000,
  maxDrawdownPercent: 20,
  dailyResetHourUtc: 0,
  maxOpportunitiesPerCycle: 3,
  logIntervalMs: 60000,
};
