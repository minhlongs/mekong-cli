/**
 * Growth Analyzer — MoM/WoW growth, churn, NRR.
 * Phase 4 of v0.8 Analytics.
 */
import type { GrowthIndicator, AnalyticsPeriod } from './types.js';

export interface GrowthInputs {
  period: AnalyticsPeriod;
  /** MRR for this period */
  currentMRR: number;
  /** MRR for prior month */
  previousMRR: number;
  /** Revenue this week */
  currentWeekRevenue: number;
  /** Revenue prior week */
  previousWeekRevenue: number;
  /** Customers active at start of period */
  startingCustomers: number;
  /** New customers acquired */
  newCustomers: number;
  /** Customers who cancelled */
  churnedCustomers: number;
  /** Expansion revenue (upsells this period) */
  expansionRevenue: number;
}

export class GrowthAnalyzer {
  /**
   * Compute growth indicators from period-over-period MRR/customer data.
   * NRR = (startMRR + expansion - churn_value) / startMRR * 100
   */
  analyze(inputs: GrowthInputs): GrowthIndicator {
    const {
      period,
      currentMRR,
      previousMRR,
      currentWeekRevenue,
      previousWeekRevenue,
      startingCustomers,
      newCustomers,
      churnedCustomers,
      expansionRevenue,
    } = inputs;

    const momGrowthPercent = previousMRR > 0
      ? ((currentMRR - previousMRR) / previousMRR) * 100
      : currentMRR > 0 ? 100 : 0;

    const wowGrowthPercent = previousWeekRevenue > 0
      ? ((currentWeekRevenue - previousWeekRevenue) / previousWeekRevenue) * 100
      : currentWeekRevenue > 0 ? 100 : 0;

    // Churn rate: churned / starting customers
    const churnRate = startingCustomers > 0
      ? churnedCustomers / startingCustomers
      : 0;

    // NRR: net revenue retention
    // If previous MRR = 0, NRR is undefined — return 100 as neutral baseline
    const nrrPercent = previousMRR > 0
      ? ((currentMRR + expansionRevenue) / previousMRR) * 100
      : 100;

    return {
      period,
      momGrowthPercent: Math.round(momGrowthPercent * 100) / 100,
      wowGrowthPercent: Math.round(wowGrowthPercent * 100) / 100,
      churnRate: Math.round(churnRate * 10000) / 10000,
      expansionRevenue: Math.round(expansionRevenue * 100) / 100,
      nrrPercent: Math.round(nrrPercent * 100) / 100,
      newCustomers,
      churnedCustomers,
      computedAt: new Date().toISOString(),
    };
  }

  /** Format for CLI display */
  formatSummary(g: GrowthIndicator): string {
    const sign = (n: number) => (n >= 0 ? '+' : '');
    const lines = [
      `\nGrowth Trends — ${g.period.label}\n`,
      `  MoM Growth       : ${sign(g.momGrowthPercent)}${g.momGrowthPercent.toFixed(1)}%`,
      `  WoW Growth       : ${sign(g.wowGrowthPercent)}${g.wowGrowthPercent.toFixed(1)}%`,
      `  Churn Rate       : ${(g.churnRate * 100).toFixed(2)}%`,
      `  Expansion Rev    : $${g.expansionRevenue.toFixed(2)}`,
      `  NRR              : ${g.nrrPercent.toFixed(1)}%`,
      `  New Customers    : ${g.newCustomers}`,
      `  Churned          : ${g.churnedCustomers}`,
      '',
    ];
    return lines.join('\n');
  }
}
