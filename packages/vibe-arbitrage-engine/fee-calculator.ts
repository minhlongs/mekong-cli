/**
 * FeeCalculator — Exchange-specific fee tier calculation.
 */

import {
  FeeTier, ExchangeFeeSchedule, FeeBreakdown,
  ArbitrageFeeReport, DEFAULT_FEE_SCHEDULES,
} from './fee-calculator-tiers';

export * from './fee-calculator-tiers';

export class FeeCalculator {
  private schedules: Map<string, ExchangeFeeSchedule> = new Map();
  private vipLevels: Map<string, string> = new Map();

  constructor() {
    for (const schedule of DEFAULT_FEE_SCHEDULES) {
      this.schedules.set(schedule.exchange, schedule);
    }
  }

  setSchedule(schedule: ExchangeFeeSchedule): void {
    this.schedules.set(schedule.exchange, schedule);
  }

  setVipLevel(exchange: string, level: string): void {
    this.vipLevels.set(exchange, level);
  }

  getTier(exchange: string): FeeTier {
    const schedule = this.schedules.get(exchange);
    if (!schedule) {
      return { level: 'Unknown', makerRate: 0.001, takerRate: 0.001, minVolume30d: 0 };
    }

    const vipLevel = this.vipLevels.get(exchange);
    if (vipLevel) {
      const tier = schedule.tiers.find(t => t.level === vipLevel);
      if (tier) return tier;
    }

    return schedule.tiers[0];
  }

  calculateFee(
    exchange: string,
    side: 'buy' | 'sell',
    priceUsd: number,
    amountBase: number,
    orderType: 'maker' | 'taker' = 'taker'
  ): FeeBreakdown {
    const tier = this.getTier(exchange);
    const rate = orderType === 'maker' ? tier.makerRate : tier.takerRate;
    const notionalUsd = priceUsd * amountBase;
    const feeUsd = notionalUsd * rate;
    const feeBase = amountBase * rate;

    return { exchange, side, orderType, rate, feeUsd, feeBase };
  }

  calculateArbitrageFees(
    buyExchange: string,
    sellExchange: string,
    symbol: string,
    buyPrice: number,
    sellPrice: number,
    amountBase: number,
    includeWithdrawal: boolean = false
  ): ArbitrageFeeReport {
    const buyFee = this.calculateFee(buyExchange, 'buy', buyPrice, amountBase);
    const sellFee = this.calculateFee(sellExchange, 'sell', sellPrice, amountBase);

    let withdrawalFeeUsd = 0;
    if (includeWithdrawal) {
      const baseCurrency = symbol.split('/')[0];
      withdrawalFeeUsd = this.getWithdrawalFee(buyExchange, baseCurrency) * buyPrice;
    }

    const totalFeesUsd = buyFee.feeUsd + sellFee.feeUsd;
    const totalCostUsd = totalFeesUsd + withdrawalFeeUsd;

    const avgPrice = (buyPrice + sellPrice) / 2;
    const notional = avgPrice * amountBase;
    const breakEvenSpreadPercent = notional > 0 ? (totalCostUsd / notional) * 100 : 0;

    return {
      buyFee, sellFee, totalFeesUsd,
      withdrawalFeeUsd, totalCostUsd, breakEvenSpreadPercent,
    };
  }

  getWithdrawalFee(exchange: string, currency: string): number {
    const schedule = this.schedules.get(exchange);
    if (!schedule) return 0;
    return schedule.withdrawalFees.get(currency) || 0;
  }

  calculateNetProfit(
    buyExchange: string,
    sellExchange: string,
    symbol: string,
    buyPrice: number,
    sellPrice: number,
    amountBase: number,
    slippageCostUsd: number = 0
  ): { grossProfitUsd: number; totalCostsUsd: number; netProfitUsd: number; profitable: boolean } {
    const feeReport = this.calculateArbitrageFees(
      buyExchange, sellExchange, symbol, buyPrice, sellPrice, amountBase
    );

    const grossProfitUsd = (sellPrice - buyPrice) * amountBase;
    const totalCostsUsd = feeReport.totalCostUsd + slippageCostUsd;
    const netProfitUsd = grossProfitUsd - totalCostsUsd;

    return {
      grossProfitUsd, totalCostsUsd, netProfitUsd,
      profitable: netProfitUsd > 0,
    };
  }

  compareFees(priceUsd: number, amountBase: number): { exchange: string; takerFeeUsd: number; makerFeeUsd: number }[] {
    const results: { exchange: string; takerFeeUsd: number; makerFeeUsd: number }[] = [];

    for (const exchange of this.schedules.keys()) {
      const takerFee = this.calculateFee(exchange, 'buy', priceUsd, amountBase, 'taker');
      const makerFee = this.calculateFee(exchange, 'buy', priceUsd, amountBase, 'maker');
      results.push({
        exchange,
        takerFeeUsd: takerFee.feeUsd,
        makerFeeUsd: makerFee.feeUsd,
      });
    }

    return results.sort((a, b) => a.takerFeeUsd - b.takerFeeUsd);
  }

  getExchanges(): string[] {
    return Array.from(this.schedules.keys());
  }
}
