/**
 * @agencyos/vibe-billing-trading — Fee Calculator Hook
 *
 * Framework-agnostic hook wrapping FeeCalculator from trading-core.
 * Provides stateful fee tier management + convenience methods for
 * arbitrage cost analysis across exchanges.
 *
 * Usage:
 *   import { createFeeCalculatorHook } from '@agencyos/vibe-billing-trading/fee-hook';
 *   const fees = createFeeCalculatorHook({ vipLevels: { binance: 'VIP1' } });
 *   const report = fees.calculateArbitrageCost('binance', 'okx', 'BTC/USDT', 60000, 60100, 0.5);
 */

import {
  FeeCalculator,
  type FeeTier,
  type FeeBreakdown,
  type ArbitrageFeeReport,
  type ExchangeFeeSchedule,
} from '@agencyos/trading-core/arbitrage';

// ─── Config ─────────────────────────────────────────────────────

export interface FeeCalculatorHookConfig {
  /** Exchange → VIP level mapping (e.g., { binance: 'VIP1', okx: 'Regular' }) */
  vipLevels?: Record<string, string>;
  /** Custom fee schedules to override defaults */
  customSchedules?: ExchangeFeeSchedule[];
}

// ─── Hook Return Type ───────────────────────────────────────────

export interface FeeCalculatorHook {
  /** Get fee tier for an exchange */
  getTier(exchange: string): FeeTier;
  /** Calculate single trade fee */
  calculateFee(exchange: string, side: 'buy' | 'sell', priceUsd: number, amountBase: number, orderType?: 'maker' | 'taker'): FeeBreakdown;
  /** Calculate full arbitrage cost (buy + sell + optional withdrawal) */
  calculateArbitrageCost(buyExchange: string, sellExchange: string, symbol: string, buyPrice: number, sellPrice: number, amountBase: number, includeWithdrawal?: boolean): ArbitrageFeeReport;
  /** Calculate net profit after all costs */
  calculateNetProfit(buyExchange: string, sellExchange: string, symbol: string, buyPrice: number, sellPrice: number, amountBase: number, slippageCostUsd?: number): { grossProfitUsd: number; totalCostsUsd: number; netProfitUsd: number; profitable: boolean };
  /** Compare fees across all exchanges for given trade size */
  compareFees(priceUsd: number, amountBase: number): { exchange: string; takerFeeUsd: number; makerFeeUsd: number }[];
  /** Find cheapest exchange for a given trade size */
  findCheapestExchange(priceUsd: number, amountBase: number): { exchange: string; takerFeeUsd: number } | null;
  /** Get break-even spread % needed to profit on an arb trade */
  getBreakEvenSpread(buyExchange: string, sellExchange: string, priceUsd: number, amountBase: number): number;
  /** Update VIP level for an exchange */
  setVipLevel(exchange: string, level: string): void;
  /** Add/override fee schedule */
  setSchedule(schedule: ExchangeFeeSchedule): void;
  /** List registered exchanges */
  getExchanges(): string[];
}

// ─── Factory ────────────────────────────────────────────────────

export function createFeeCalculatorHook(config?: FeeCalculatorHookConfig): FeeCalculatorHook {
  const calc = new FeeCalculator();

  // Apply custom schedules
  if (config?.customSchedules) {
    for (const schedule of config.customSchedules) {
      calc.setSchedule(schedule);
    }
  }

  // Apply VIP levels
  if (config?.vipLevels) {
    for (const [exchange, level] of Object.entries(config.vipLevels)) {
      calc.setVipLevel(exchange, level);
    }
  }

  return {
    getTier: (exchange) => calc.getTier(exchange),

    calculateFee: (exchange, side, priceUsd, amountBase, orderType = 'taker') =>
      calc.calculateFee(exchange, side, priceUsd, amountBase, orderType),

    calculateArbitrageCost: (buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, includeWithdrawal = false) =>
      calc.calculateArbitrageFees(buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, includeWithdrawal),

    calculateNetProfit: (buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, slippageCostUsd = 0) =>
      calc.calculateNetProfit(buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase, slippageCostUsd),

    compareFees: (priceUsd, amountBase) => calc.compareFees(priceUsd, amountBase),

    findCheapestExchange(priceUsd: number, amountBase: number) {
      const results = calc.compareFees(priceUsd, amountBase);
      return results.length > 0 ? { exchange: results[0].exchange, takerFeeUsd: results[0].takerFeeUsd } : null;
    },

    getBreakEvenSpread(buyExchange: string, sellExchange: string, priceUsd: number, amountBase: number) {
      const report = calc.calculateArbitrageFees(buyExchange, sellExchange, 'X/USDT', priceUsd, priceUsd, amountBase);
      return report.breakEvenSpreadPercent;
    },

    setVipLevel: (exchange, level) => calc.setVipLevel(exchange, level),
    setSchedule: (schedule) => calc.setSchedule(schedule),
    getExchanges: () => calc.getExchanges(),
  };
}
