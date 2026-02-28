/**
 * @agencyos/vibe-billing-trading — Arbitrage Billing Hook (Composite)
 *
 * Combines FeeCalculator + ProfitTracker into a single unified hook
 * for complete arbitrage billing lifecycle: cost analysis → execution → tracking.
 *
 * Usage:
 *   import { createArbitrageBillingHook } from '@agencyos/vibe-billing-trading/arbitrage-billing-hook';
 *   const billing = createArbitrageBillingHook({ initialEquity: 10000, vipLevels: { binance: 'VIP1' } });
 *   const analysis = billing.analyzeOpportunity('binance', 'okx', 'BTC/USDT', 60000, 60100, 0.5);
 *   if (analysis.profitable) billing.recordExecution(analysis.netProfitUsd);
 */

import { createFeeCalculatorHook, type FeeCalculatorHookConfig, type FeeCalculatorHook } from './fee-calculator-hook';
import { createProfitTrackerHook, type ProfitTrackerHookConfig, type ProfitTrackerHook } from './profit-tracker-hook';

// ─── Config ─────────────────────────────────────────────────────

export interface ArbitrageBillingHookConfig extends FeeCalculatorHookConfig, ProfitTrackerHookConfig {}

// ─── Opportunity Analysis ───────────────────────────────────────

export interface OpportunityAnalysis {
  buyExchange: string;
  sellExchange: string;
  symbol: string;
  spreadPercent: number;
  grossProfitUsd: number;
  totalFeesUsd: number;
  slippageCostUsd: number;
  netProfitUsd: number;
  profitable: boolean;
  breakEvenSpreadPercent: number;
  marginOfSafety: number; // spread above break-even (percentage points)
}

// ─── Session Report ─────────────────────────────────────────────

export interface TradingSessionReport {
  equity: number;
  pnl: number;
  pnlPercent: number;
  winRate: number;
  trades: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
  shouldHalt: boolean;
  alerts: number;
}

// ─── Hook Return Type ───────────────────────────────────────────

export interface ArbitrageBillingHook {
  /** Access underlying fee calculator hook */
  fees: FeeCalculatorHook;
  /** Access underlying profit tracker hook */
  tracker: ProfitTrackerHook;
  /** Analyze an arbitrage opportunity — returns full cost/profit breakdown */
  analyzeOpportunity(buyExchange: string, sellExchange: string, symbol: string, buyPrice: number, sellPrice: number, amountBase: number, slippageCostUsd?: number): OpportunityAnalysis;
  /** Record an executed trade result into profit tracker */
  recordExecution(pnl: number): void;
  /** Get trading session report (combines fee + tracker metrics) */
  getSessionReport(): TradingSessionReport;
  /** Check if opportunity meets minimum profitability threshold */
  meetsThreshold(analysis: OpportunityAnalysis, minNetProfitUsd?: number, minMarginOfSafety?: number): boolean;
  /** Reset session (profit tracker only — fee config preserved) */
  resetSession(): void;
}

// ─── Factory ────────────────────────────────────────────────────

export function createArbitrageBillingHook(config?: ArbitrageBillingHookConfig): ArbitrageBillingHook {
  const fees = createFeeCalculatorHook(config);
  const tracker = createProfitTrackerHook(config);

  return {
    fees,
    tracker,

    analyzeOpportunity(buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, slippageCostUsd = 0) {
      const feeReport = fees.calculateArbitrageCost(buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase);
      const netResult = fees.calculateNetProfit(buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, slippageCostUsd);

      const avgPrice = (buyPrice + sellPrice) / 2;
      const spreadPercent = avgPrice > 0 ? ((sellPrice - buyPrice) / avgPrice) * 100 : 0;
      const marginOfSafety = spreadPercent - feeReport.breakEvenSpreadPercent;

      return {
        buyExchange,
        sellExchange,
        symbol,
        spreadPercent,
        grossProfitUsd: netResult.grossProfitUsd,
        totalFeesUsd: feeReport.totalFeesUsd,
        slippageCostUsd,
        netProfitUsd: netResult.netProfitUsd,
        profitable: netResult.profitable,
        breakEvenSpreadPercent: feeReport.breakEvenSpreadPercent,
        marginOfSafety,
      };
    },

    recordExecution(pnl) {
      tracker.recordTrade(pnl);
    },

    getSessionReport() {
      const summary = tracker.getSummary();
      return {
        equity: summary.currentEquity,
        pnl: summary.cumulativePnl,
        pnlPercent: summary.cumulativePnlPercent,
        winRate: summary.winRate,
        trades: summary.totalTrades,
        maxDrawdown: summary.maxDrawdownPercent,
        sharpeRatio: summary.sharpeRatio,
        profitFactor: summary.profitFactor,
        shouldHalt: tracker.shouldHalt(),
        alerts: tracker.getAlerts().length,
      };
    },

    meetsThreshold(analysis, minNetProfitUsd = 0.5, minMarginOfSafety = 0.05) {
      return analysis.profitable
        && analysis.netProfitUsd >= minNetProfitUsd
        && analysis.marginOfSafety >= minMarginOfSafety;
    },

    resetSession() {
      tracker.reset();
    },
  };
}
