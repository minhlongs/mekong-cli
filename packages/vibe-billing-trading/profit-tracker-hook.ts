/**
 * @agencyos/vibe-billing-trading — Profit Tracker Hook
 *
 * Framework-agnostic hook wrapping ProfitTracker from trading-core.
 * Provides stateful equity tracking, drawdown alerts, and performance
 * metrics for arbitrage sessions.
 *
 * Usage:
 *   import { createProfitTrackerHook } from '@agencyos/vibe-billing-trading/profit-hook';
 *   const tracker = createProfitTrackerHook({ initialEquity: 10000 });
 *   tracker.recordTrade(25.50);
 *   const summary = tracker.getSummary();
 */

import {
  ProfitTracker,
  type ProfitTrackerConfig,
  type EquityPoint,
  type DrawdownAlert,
  type PerformanceSummary,
} from '@agencyos/trading-core/arbitrage';

// ─── Config ─────────────────────────────────────────────────────

export interface ProfitTrackerHookConfig extends Partial<ProfitTrackerConfig> {
  /** Max drawdown % before shouldHalt returns true (default: 20) */
  haltDrawdownPercent?: number;
}

// ─── Hook Return Type ───────────────────────────────────────────

export interface ProfitTrackerHook {
  /** Record a trade P&L (positive = win, negative = loss) */
  recordTrade(pnl: number): void;
  /** Get full performance summary */
  getSummary(): PerformanceSummary;
  /** Get equity curve data points */
  getEquityCurve(): EquityPoint[];
  /** Get current drawdown % from peak */
  getCurrentDrawdown(): number;
  /** Check if trading should halt due to excessive drawdown */
  shouldHalt(): boolean;
  /** Get all triggered drawdown alerts */
  getAlerts(): DrawdownAlert[];
  /** Register callback for drawdown alerts */
  onDrawdownAlert(callback: (alert: DrawdownAlert) => void): void;
  /** Print formatted performance report to logger */
  printReport(): void;
  /** Reset tracker to initial state */
  reset(): void;
  /** Get quick P&L snapshot (current equity, cumulative P&L, win rate) */
  getSnapshot(): { equity: number; pnl: number; pnlPercent: number; winRate: number; trades: number; drawdown: number };
  /** Check if session is profitable */
  isProfitable(): boolean;
}

// ─── Factory ────────────────────────────────────────────────────

export function createProfitTrackerHook(config?: ProfitTrackerHookConfig): ProfitTrackerHook {
  const { haltDrawdownPercent = 20, ...trackerConfig } = config ?? {};
  const tracker = new ProfitTracker(trackerConfig);

  return {
    recordTrade: (pnl) => tracker.recordTrade(pnl),
    getSummary: () => tracker.getSummary(),
    getEquityCurve: () => tracker.getEquityCurve(),
    getCurrentDrawdown: () => tracker.getCurrentDrawdown(),
    shouldHalt: () => tracker.shouldHalt(haltDrawdownPercent),
    getAlerts: () => tracker.getAlerts(),
    onDrawdownAlert: (callback) => tracker.onDrawdownAlert(callback),
    printReport: () => tracker.printReport(),
    reset: () => tracker.reset(),

    getSnapshot() {
      const s = tracker.getSummary();
      return {
        equity: s.currentEquity,
        pnl: s.cumulativePnl,
        pnlPercent: s.cumulativePnlPercent,
        winRate: s.winRate,
        trades: s.totalTrades,
        drawdown: s.maxDrawdownPercent,
      };
    },

    isProfitable() {
      return tracker.getSummary().cumulativePnl > 0;
    },
  };
}
