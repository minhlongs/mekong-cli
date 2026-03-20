/**
 * Arbitrage Engine Types
 * Phase 2: Multi-exchange arbitrage trading
 */

export type ExchangeId = 'binance' | 'coinbase' | 'kraken' | 'uniswap';

export interface PricePoint {
  exchange: ExchangeId;
  symbol: string;
  bid: number;
  ask: number;
  timestamp: number;
  volume24h?: number;
}

export interface OrderBookLevel {
  price: number;
  amount: number;
}

export interface OrderBook {
  exchange: ExchangeId;
  symbol: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  timestamp: number;
}

export interface ArbitrageOpportunity {
  id: string;
  type: 'triangular' | 'dex-cex' | 'funding-rate' | 'cross-exchange';
  legs: ArbitrageLeg[];
  expectedProfit: number;
  expectedProfitPct: number;
  totalFees: number;
  gasFee?: number;
  slippage?: number;
  confidence: number;
  detectedAt: number;
  expiresAt: number;
}

export interface ArbitrageLeg {
  exchange: ExchangeId;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  amount: number;
  fee: number;
}

export interface ExecutionResult {
  opportunityId: string;
  success: boolean;
  executedLegs: ExecutedLeg[];
  actualProfit: number;
  actualProfitPct: number;
  totalFees: number;
  error?: string;
  executedAt: number;
}

export interface ExecutedLeg {
  exchange: ExchangeId;
  symbol: string;
  side: 'buy' | 'sell';
  executedPrice: number;
  executedAmount: number;
  fee: number;
  txHash?: string;
}

export interface BacktestConfig {
  startDate: Date;
  endDate: Date;
  initialCapital: number;
  exchanges: ExchangeId[];
  symbols: string[];
  minProfitThreshold: number;
  maxPositionSize: number;
}

export interface BacktestResult {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  totalProfit: number;
  totalLoss: number;
  netProfit: number;
  netProfitPct: number;
  sharpeRatio: number;
  maxDrawdown: number;
  avgTradeDuration: number;
  opportunities: OpportunityMetric[];
}

export interface OpportunityMetric {
  timestamp: number;
  type: string;
  expectedProfit: number;
  executed: boolean;
}

export interface ScannerConfig {
  exchanges: ExchangeId[];
  symbols: string[];
  pollIntervalMs: number;
  minVolume24h: number;
}

export interface DetectorConfig {
  minProfitThreshold: number;
  maxSlippageTolerance: number;
  supportedTypes: Array<'triangular' | 'dex-cex' | 'funding-rate' | 'cross-exchange'>;
}

export interface ExecutorConfig {
  dryRun: boolean;
  maxPositionSize: number;
  slippageTolerance: number;
  minProfitThreshold: number;
  timeoutMs: number;
}

export interface ExecutionEngineConfig {
  dryRun?: boolean;
  timeoutMs?: number;
}

export class ExecutionEngine {
  constructor(config?: ExecutionEngineConfig) {
    // Implementation placeholder
  }

  async execute(opportunity: ArbitrageOpportunity): Promise<any> {
    // Implementation placeholder
    return { success: true, actualProfit: 0, actualProfitPct: 0, totalFees: 0 };
  }
}
