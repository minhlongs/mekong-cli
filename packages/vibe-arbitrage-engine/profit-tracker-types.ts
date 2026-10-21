/**
 * ProfitTracker types and default configuration.
 */

export interface EquityPoint {
  timestamp: number;
  equity: number;           // Current equity value (initial + cumulative P&L)
  pnl: number;              // P&L for this trade
  cumulativePnl: number;    // Running total P&L
  drawdownPercent: number;  // Current drawdown from peak (negative = drawdown)
  tradeId: number;
}

export interface DrawdownAlert {
  timestamp: number;
  drawdownPercent: number;
  peakEquity: number;
  currentEquity: number;
  threshold: string;        // Which threshold triggered (e.g., "5%", "10%")
}

export interface PerformanceSummary {
  initialEquity: number;
  currentEquity: number;
  cumulativePnl: number;
  cumulativePnlPercent: number;
  maxDrawdownPercent: number;
  maxDrawdownUsd: number;
  peakEquity: number;
  troughEquity: number;
  sharpeRatio: number;
  sortinoRatio: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  recoveryFactor: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  uptimeMs: number;
}

export interface ProfitTrackerConfig {
  initialEquity: number;              // Starting equity (default: 10000)
  drawdownAlertThresholds: number[];  // Drawdown % levels that trigger alerts (default: [5, 10, 20])
  sharpeWindowSize: number;           // Rolling window for Sharpe calculation (default: 30 trades)
  riskFreeRate: number;               // Annual risk-free rate for Sharpe (default: 0.05)
  maxEquityPoints: number;            // Max equity points to keep (default: 10000)
}

export const DEFAULT_PROFIT_TRACKER_CONFIG: ProfitTrackerConfig = {
  initialEquity: 10000,
  drawdownAlertThresholds: [5, 10, 20],
  sharpeWindowSize: 30,
  riskFreeRate: 0.05,
  maxEquityPoints: 10000,
};
