/**
 * analytics-bundle.ts — Data aggregation bundle builder for ROI analytics CLI.
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { ROICalculator, currentMonthPeriod, monthPeriod } from '../../analytics/roi-calculator.js';
import { AgentScorer } from '../../analytics/agent-scorer.js';
import { RevenueTracker } from '../../analytics/revenue-tracker.js';
import { GrowthAnalyzer } from '../../analytics/growth-analyzer.js';
import { MeteringStore } from '../../metering/store.js';
import { ReceiptStore } from '../../payments/receipt-store.js';
import { ExecutionFeedback } from '../../self-improve/execution-feedback.js';
import type { AnalyticsBundle } from '../../analytics/types.js';

export const DEFAULT_METERING_DIR = join(homedir(), '.mekong', 'metering');
export const DEFAULT_RECEIPTS_PATH = join(homedir(), '.mekong', 'payments', 'receipts.jsonl');
export const DEFAULT_FEEDBACK_DIR = join(homedir(), '.mekong', 'self-improve');

export const HOURLY_RATE = Number(process.env['MEKONG_HOURLY_RATE'] ?? '100');

export async function buildBundle(): Promise<AnalyticsBundle> {
  const period = currentMonthPeriod();
  const prevPeriod = monthPeriod(-1);

  const meteringStore = new MeteringStore(DEFAULT_METERING_DIR);
  const meteringResult = await meteringStore.queryRange(period.startDate, period.endDate);
  let totalCost = 0;
  if (meteringResult.ok) {
    for (const event of meteringResult.value) {
      totalCost += event.estimatedCost ?? 0;
    }
  }

  const receiptStore = new ReceiptStore(DEFAULT_RECEIPTS_PATH);
  const receiptsResult = await receiptStore.readAll();
  const events = receiptsResult.ok ? receiptsResult.value : [];

  const revenueTracker = new RevenueTracker();
  const revenueResult = revenueTracker.buildReport(events, period);
  const revenue = revenueResult.ok
    ? revenueResult.value
    : revenueTracker.buildFromMRR({
      mrr: 0,
      activeCustomers: 0,
      tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 },
      period,
    });

  const feedback = new ExecutionFeedback(DEFAULT_FEEDBACK_DIR);
  const records = await feedback.loadRecords();
  const periodStart = new Date(period.startDate).getTime();
  const periodEnd = new Date(period.endDate).getTime();
  const periodRecords = records.filter((r) => {
    const t = new Date(r.timestamp).getTime();
    return t >= periodStart && t <= periodEnd;
  });
  const successfulRecs = periodRecords.filter((r) => r.result === 'success');
  const timeSavedHours = successfulRecs.length * 0.5;

  const roi = new ROICalculator().calculate({
    timeSavedHours,
    hourlyRate: HOURLY_RATE,
    revenueGenerated: revenue.mrr,
    totalCost,
    period,
  });

  const byAgent = new Map<string, typeof periodRecords>();
  for (const r of periodRecords) {
    const list = byAgent.get(r.agentName) ?? [];
    list.push(r);
    byAgent.set(r.agentName, list);
  }
  const scorer = new AgentScorer();
  const agents = scorer.scoreAll(
    Array.from(byAgent.entries()).map(([agentName, recs]) => {
      const succeeded = recs.filter((r) => r.result === 'success').length;
      const failed = recs.filter((r) => r.result === 'failure').length;
      const partial = recs.filter((r) => r.result === 'partial').length;
      return {
        agentName,
        phasesCompleted: succeeded,
        totalPhases: recs.length,
        recentCommits: succeeded,
        activityBaseline: Math.max(10, recs.length),
        totalExecutions: recs.length,
        successfulExecutions: succeeded,
        recoveredExecutions: partial,
        failedExecutions: failed,
      };
    }),
  );

  const prevRevenueResult = revenueTracker.buildReport(events, prevPeriod);
  const prevRevenue = prevRevenueResult.ok
    ? prevRevenueResult.value
    : revenueTracker.buildFromMRR({
      mrr: 0,
      activeCustomers: 0,
      tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 },
      period: prevPeriod,
    });
  const growth = new GrowthAnalyzer().analyze({
    period,
    currentMRR: revenue.mrr,
    previousMRR: prevRevenue.mrr,
    currentWeekRevenue: revenue.mrr / 4,
    previousWeekRevenue: prevRevenue.mrr / 4,
    startingCustomers: prevRevenue.activeCustomers,
    newCustomers: Math.max(0, revenue.activeCustomers - prevRevenue.activeCustomers),
    churnedCustomers: 0,
    expansionRevenue: 0,
  });

  return {
    roi: roi.ok ? roi.value : {
      roiPercent: 0,
      timeSavedHours,
      hourlyRate: HOURLY_RATE,
      timeSavedValue: 0,
      revenueGenerated: 0,
      totalCost,
      netValue: 0,
      period,
      computedAt: new Date().toISOString(),
    },
    agents,
    revenue,
    growth,
  };
}
