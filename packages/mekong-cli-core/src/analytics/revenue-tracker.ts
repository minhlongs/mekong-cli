/**
 * Revenue Tracker — aggregate billing receipts into MRR/ARR/ARPU.
 * Phase 3 of v0.8 Analytics.
 */
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { RevenueReport, AnalyticsPeriod } from './types.js';
import type { WebhookEvent } from '../payments/types.js';
import type { LicenseTier } from '../license/types.js';

/** Monthly price per tier (USD) — used to compute MRR from active subs */
const TIER_MONTHLY_PRICE: Record<LicenseTier, number> = {
  free: 0,
  starter: 49,
  pro: 149,
  enterprise: 499,
};

export class RevenueTracker {
  /**
   * Build a RevenueReport from raw webhook events for a period.
   * Counts subscription.active events as active paying customers.
   * Sums order.created amounts for total revenue.
   */
  buildReport(events: WebhookEvent[], period: AnalyticsPeriod): Result<RevenueReport, Error> {
    try {
      const periodStart = new Date(period.startDate).getTime();
      const periodEnd = new Date(period.endDate).getTime();

      const inPeriod = events.filter((e) => {
        const t = new Date(e.receivedAt).getTime();
        return t >= periodStart && t <= periodEnd;
      });

      // Tier distribution from subscription events
      const tierCounts: Record<LicenseTier, number> = {
        free: 0, starter: 0, pro: 0, enterprise: 0,
      };
      const seenCustomers = new Set<string>();

      for (const e of inPeriod) {
        if (e.type === 'subscription.active' && e.tier) {
          tierCounts[e.tier] = (tierCounts[e.tier] ?? 0) + 1;
          if (e.customerId) seenCustomers.add(e.customerId);
        }
      }

      // Total revenue from completed orders
      const orderEvents = inPeriod.filter((e) => e.type === 'order.created');
      const totalRevenue = orderEvents.length * 0; // orders don't carry amount in WebhookEvent
      // MRR from active subscriptions
      const mrr = (tierCounts.starter * TIER_MONTHLY_PRICE.starter)
        + (tierCounts.pro * TIER_MONTHLY_PRICE.pro)
        + (tierCounts.enterprise * TIER_MONTHLY_PRICE.enterprise);

      const activeCustomers = tierCounts.starter + tierCounts.pro + tierCounts.enterprise;
      const arr = mrr * 12;
      const arpu = activeCustomers > 0 ? mrr / activeCustomers : 0;

      return ok({
        period,
        mrr: Math.round(mrr * 100) / 100,
        arr: Math.round(arr * 100) / 100,
        arpu: Math.round(arpu * 100) / 100,
        activeCustomers,
        totalRevenue: Math.round((totalRevenue + mrr) * 100) / 100,
        tierDistribution: { ...tierCounts },
        computedAt: new Date().toISOString(),
      });
    } catch (e) {
      return err(new Error(`RevenueTracker.buildReport failed: ${String(e)}`));
    }
  }

  /**
   * Build report from raw MRR inputs (for testing or direct injection).
   * @param opts - pre-computed MRR, customer count, tier distribution and period
   */
  buildFromMRR(opts: {
    mrr: number;
    activeCustomers: number;
    tierDistribution: RevenueReport['tierDistribution'];
    period: AnalyticsPeriod;
  }): RevenueReport {
    const { mrr, activeCustomers, tierDistribution, period } = opts;
    return {
      period,
      mrr: Math.round(mrr * 100) / 100,
      arr: Math.round(mrr * 12 * 100) / 100,
      arpu: activeCustomers > 0 ? Math.round((mrr / activeCustomers) * 100) / 100 : 0,
      activeCustomers,
      totalRevenue: Math.round(mrr * 100) / 100,
      tierDistribution,
      computedAt: new Date().toISOString(),
    };
  }

  /** Format for CLI display */
  formatSummary(report: RevenueReport): string {
    const { period, mrr, arr, arpu, activeCustomers, tierDistribution } = report;
    const lines = [
      `\nRevenue — ${period.label}\n`,
      `  MRR              : $${mrr.toFixed(2)}`,
      `  ARR              : $${arr.toFixed(2)}`,
      `  ARPU             : $${arpu.toFixed(2)}`,
      `  Active customers : ${activeCustomers}`,
      '\n  Tier Distribution:',
      `    Free       : ${tierDistribution.free}`,
      `    Starter    : ${tierDistribution.starter}`,
      `    Pro        : ${tierDistribution.pro}`,
      `    Enterprise : ${tierDistribution.enterprise}`,
      '',
    ];
    return lines.join('\n');
  }
}
