/**
 * ArbitrageBacktester types, metrics, and default configuration.
 */

export interface ExchangePricePoint {
  exchange: string;
  price: number;
}

export interface MultiExchangePriceSnapshot {
  symbol: string;
  timestamp: number;
  prices: ExchangePricePoint[];
}

export interface BacktestTradeRecord {
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
  slippageCostUsd: number;
  netProfitUsd: number;
  equityAfter: number;
}

export interface BacktestEquityPoint {
  timestamp: number;
  equity: number;
  drawdownPercent: number;
}

export interface BacktestResult {
  config: BacktestConfig;
  trades: BacktestTradeRecord[];
  equityCurve: BacktestEquityPoint[];
  metrics: BacktestMetrics;
}

export interface BacktestMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalProfitUsd: number;
  totalFeesUsd: number;
  netProfitUsd: number;
  maxDrawdownPercent: number;
  sharpeRatio: number;
  profitFactor: number;
  avgTradeUsd: number;
  avgWinUsd: number;
  avgLossUsd: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  returnOnCapital: number;
}

export interface BacktestConfig {
  initialCapitalUsd: number;
  positionSizeUsd: number;
  minSpreadPercent: number;
  slippageBps: number;
  cooldownMs: number;
  maxDailyLossUsd: number;
  useFeeCalculator: boolean;
  flatFeeRate: number;
}

export const DEFAULT_BACKTEST_CONFIG: BacktestConfig = {
  initialCapitalUsd: 10000,
  positionSizeUsd: 1000,
  minSpreadPercent: 0.1,
  slippageBps: 5,
  cooldownMs: 5000,
  maxDailyLossUsd: 200,
  useFeeCalculator: true,
  flatFeeRate: 0.001,
};

export function createEmptyBacktestMetrics(): BacktestMetrics {
  return {
    totalTrades: 0, winningTrades: 0, losingTrades: 0, winRate: 0, totalProfitUsd: 0,
    totalFeesUsd: 0, netProfitUsd: 0, maxDrawdownPercent: 0, sharpeRatio: 0, profitFactor: 0,
    avgTradeUsd: 0, avgWinUsd: 0, avgLossUsd: 0, maxConsecutiveWins: 0, maxConsecutiveLosses: 0, returnOnCapital: 0,
  };
}
