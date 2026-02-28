/**
 * @agencyos/vibe-billing-trading — Arbitrage Billing Hooks SDK
 *
 * Reusable, framework-agnostic hooks for trading fee calculation,
 * profit tracking, and arbitrage cost analysis across exchanges.
 *
 * Built on @agencyos/trading-core primitives (FeeCalculator, ProfitTracker).
 *
 * Hooks:
 *   createFeeCalculatorHook   — Exchange fee tiers, arb cost, cheapest exchange
 *   createProfitTrackerHook   — Equity curve, drawdown alerts, Sharpe/Sortino
 *   createArbitrageBillingHook — Composite: fees + tracking in one hook
 */

export { createFeeCalculatorHook } from './fee-calculator-hook';
export type { FeeCalculatorHookConfig, FeeCalculatorHook } from './fee-calculator-hook';

export { createProfitTrackerHook } from './profit-tracker-hook';
export type { ProfitTrackerHookConfig, ProfitTrackerHook } from './profit-tracker-hook';

export { createArbitrageBillingHook } from './arbitrage-billing-hook';
export type {
  ArbitrageBillingHookConfig,
  ArbitrageBillingHook,
  OpportunityAnalysis,
  TradingSessionReport,
} from './arbitrage-billing-hook';

// Re-export core types consumers commonly need
export type {
  FeeTier,
  FeeBreakdown,
  ArbitrageFeeReport,
  ExchangeFeeSchedule,
  EquityPoint,
  DrawdownAlert,
  PerformanceSummary,
  ProfitTrackerConfig,
} from '@agencyos/trading-core/arbitrage';
