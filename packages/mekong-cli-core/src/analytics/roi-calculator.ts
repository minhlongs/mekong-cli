/**
 * ROI Calculator — Phase 1 of v0.8 Analytics.
 * Formula: ROI = (timeSaved * hourlyRate + revGenerated - totalCost) / totalCost * 100
 */
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { ROIMetrics, AnalyticsPeriod } from './types.js';

export interface ROIInputs {
  /** Hours saved by automation (from kaizen data) */
  timeSavedHours: number;
  /** Fully-loaded hourly rate to value time savings (USD) */
  hourlyRate: number;
  /** Revenue generated through the platform (from receipts) */
  revenueGenerated: number;
  /** Total platform cost (LLM + infra) from metering */
  totalCost: number;
  period: AnalyticsPeriod;
}

export class ROICalculator {
  /**
   * Calculate ROI from combined kaizen + billing + metering data.
   * ROI% = (timeSavedValue + revenueGenerated - totalCost) / totalCost * 100
   */
  calculate(inputs: ROIInputs): Result<ROIMetrics, Error> {
    const { timeSavedHours, hourlyRate, revenueGenerated, totalCost, period } = inputs;

    if (hourlyRate < 0) return err(new Error('hourlyRate must be >= 0'));
    if (timeSavedHours < 0) return err(new Error('timeSavedHours must be >= 0'));
    if (revenueGenerated < 0) return err(new Error('revenueGenerated must be >= 0'));
    if (totalCost < 0) return err(new Error('totalCost must be >= 0'));

    const timeSavedValue = timeSavedHours * hourlyRate;
    const netValue = timeSavedValue + revenueGenerated - totalCost;

    // Avoid division by zero: if cost is 0, ROI is infinite — cap at meaningful value
    const roiPercent = totalCost > 0
      ? (netValue / totalCost) * 100
      : netValue > 0 ? 9999 : 0;

    return ok({
      roiPercent: Math.round(roiPercent * 100) / 100,
      timeSavedHours,
      hourlyRate,
      timeSavedValue: Math.round(timeSavedValue * 100) / 100,
      revenueGenerated: Math.round(revenueGenerated * 100) / 100,
      totalCost: Math.round(totalCost * 100) / 100,
      netValue: Math.round(netValue * 100) / 100,
      period,
      computedAt: new Date().toISOString(),
    });
  }

  /** Format ROI for CLI display */
  formatSummary(metrics: ROIMetrics): string {
    const lines: string[] = [
      `\nROI Analysis — ${metrics.period.label}\n`,
      `  ROI                : ${metrics.roiPercent >= 0 ? '+' : ''}${metrics.roiPercent.toFixed(1)}%`,
      `  Net Value          : $${metrics.netValue.toFixed(2)}`,
      `  Time Saved         : ${metrics.timeSavedHours.toFixed(1)}h @ $${metrics.hourlyRate}/hr = $${metrics.timeSavedValue.toFixed(2)}`,
      `  Revenue Generated  : $${metrics.revenueGenerated.toFixed(2)}`,
      `  Total Cost         : $${metrics.totalCost.toFixed(6)}`,
      '',
    ];
    return lines.join('\n');
  }
}

/** Build an AnalyticsPeriod for the current UTC calendar month. */
export function currentMonthPeriod(): AnalyticsPeriod {
  const now = new Date();
  const year = now.getUTCFullYear();
  const month = String(now.getUTCMonth() + 1).padStart(2, '0');
  const label = `${year}-${month}`;
  const startDate = `${label}-01T00:00:00.000Z`;
  const lastDay = new Date(year, now.getUTCMonth() + 1, 0).getDate();
  const endDate = `${label}-${String(lastDay).padStart(2, '0')}T23:59:59.999Z`;
  return { label, startDate, endDate };
}

/**
 * Build an AnalyticsPeriod for a relative month.
 * @param offsetMonths - 0 = current month, -1 = last month, etc.
 */
export function monthPeriod(offsetMonths: number = 0): AnalyticsPeriod {
  const now = new Date();
  // Use UTC to stay consistent with currentMonthPeriod
  const year = now.getUTCFullYear();
  const rawMonth = now.getUTCMonth() + offsetMonths; // may be negative or > 11
  const target = new Date(Date.UTC(year, rawMonth, 1));
  const tYear = target.getUTCFullYear();
  const tMonth = String(target.getUTCMonth() + 1).padStart(2, '0');
  const label = `${tYear}-${tMonth}`;
  const startDate = `${label}-01T00:00:00.000Z`;
  const lastDay = new Date(Date.UTC(tYear, target.getUTCMonth() + 1, 0)).getUTCDate();
  const endDate = `${label}-${String(lastDay).padStart(2, '0')}T23:59:59.999Z`;
  return { label, startDate, endDate };
}
