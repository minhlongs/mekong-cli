/**
 * `mekong analytics` — ROI Analytics subcommands (v0.8).
 *
 *   mekong analytics roi              ROI % with breakdown
 *   mekong analytics agents           AGI score leaderboard
 *   mekong analytics revenue          MRR/ARR/ARPU
 *   mekong analytics growth           MoM/WoW growth trends
 *   mekong analytics export <file>    Full Markdown report
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { writeFile } from 'node:fs/promises';
import type { Command } from 'commander';
import { ROICalculator, currentMonthPeriod, monthPeriod } from '../../analytics/roi-calculator.js';
import { AgentScorer } from '../../analytics/agent-scorer.js';
import { RevenueTracker } from '../../analytics/revenue-tracker.js';
import { GrowthAnalyzer } from '../../analytics/growth-analyzer.js';
import { ReportGenerator } from '../../analytics/report-generator.js';
import { MeteringStore } from '../../metering/store.js';
import { ReceiptStore } from '../../payments/receipt-store.js';
import { ExecutionFeedback } from '../../self-improve/execution-feedback.js';
import type { AnalyticsBundle } from '../../analytics/types.js';

const DEFAULT_METERING_DIR = join(homedir(), '.mekong', 'metering');
const DEFAULT_RECEIPTS_PATH = join(homedir(), '.mekong', 'payments', 'receipts.jsonl');
const DEFAULT_FEEDBACK_DIR = join(homedir(), '.mekong', 'self-improve');

const HOURLY_RATE = Number(process.env['MEKONG_HOURLY_RATE'] ?? '100');

async function buildBundle(): Promise<AnalyticsBundle> {
  const period = currentMonthPeriod();
  const prevPeriod = monthPeriod(-1);

  // --- Cost from metering (sum estimatedCost from all events in period) ---
  const meteringStore = new MeteringStore(DEFAULT_METERING_DIR);
  const meteringResult = await meteringStore.queryRange(period.startDate, period.endDate);
  let totalCost = 0;
  if (meteringResult.ok) {
    for (const event of meteringResult.value) {
      totalCost += event.estimatedCost ?? 0;
    }
  }

  // --- Revenue from receipts ---
  const receiptStore = new ReceiptStore(DEFAULT_RECEIPTS_PATH);
  const receiptsResult = await receiptStore.readAll();
  const events = receiptsResult.ok ? receiptsResult.value : [];

  const revenueTracker = new RevenueTracker();
  const revenueResult = revenueTracker.buildReport(events, period);
  const revenue = revenueResult.ok
    ? revenueResult.value
    : revenueTracker.buildFromMRR({ mrr: 0, activeCustomers: 0, tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 }, period });

  // --- Time saved from self-improve feedback ---
  const feedback = new ExecutionFeedback(DEFAULT_FEEDBACK_DIR);
  const records = await feedback.loadRecords();
  const periodStart = new Date(period.startDate).getTime();
  const periodEnd = new Date(period.endDate).getTime();
  const periodRecords = records.filter((r) => {
    const t = new Date(r.timestamp).getTime();
    return t >= periodStart && t <= periodEnd;
  });
  // Estimate time saved: each successful execution saves avg 30 min vs manual
  const successfulRecs = periodRecords.filter((r) => r.result === 'success');
  const timeSavedHours = successfulRecs.length * 0.5;

  // --- ROI ---
  const roi = new ROICalculator().calculate({
    timeSavedHours,
    hourlyRate: HOURLY_RATE,
    revenueGenerated: revenue.mrr,
    totalCost,
    period,
  });

  // --- Agent scores from feedback records ---
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

  // --- Growth (current vs prior month) ---
  const prevRevenueResult = revenueTracker.buildReport(events, prevPeriod);
  const prevRevenue = prevRevenueResult.ok ? prevRevenueResult.value : revenueTracker.buildFromMRR({
    mrr: 0, activeCustomers: 0, tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 }, period: prevPeriod,
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
      roiPercent: 0, timeSavedHours, hourlyRate: HOURLY_RATE,
      timeSavedValue: 0, revenueGenerated: 0, totalCost, netValue: 0,
      period, computedAt: new Date().toISOString(),
    },
    agents,
    revenue,
    growth,
  };
}

export function registerAnalyticsCommand(program: Command): void {
  const analytics = program
    .command('analytics')
    .description('ROI analytics dashboard — revenue, growth, agent performance');

  // ── analytics roi ─────────────────────────────────────────────────────────
  analytics
    .command('roi')
    .description('Show ROI percentage with breakdown')
    .option('--hourly-rate <rate>', 'Hourly rate for time valuation (USD)', String(HOURLY_RATE))
    .action(async (opts: { hourlyRate?: string }) => {
      const bundle = await buildBundle();
      const roi = bundle.roi;
      const sign = roi.roiPercent >= 0 ? '+' : '';
      console.log(`\nROI Analysis — ${roi.period.label}\n`);
      console.log(`  ROI                : ${sign}${roi.roiPercent.toFixed(1)}%`);
      console.log(`  Net Value          : $${roi.netValue.toFixed(2)}`);
      console.log(`  Time Saved         : ${roi.timeSavedHours.toFixed(1)}h @ $${opts.hourlyRate ?? roi.hourlyRate}/hr = $${roi.timeSavedValue.toFixed(2)}`);
      console.log(`  Revenue Generated  : $${roi.revenueGenerated.toFixed(2)}`);
      console.log(`  Total Cost         : $${roi.totalCost.toFixed(6)}`);
      console.log('');
    });

  // ── analytics agents ──────────────────────────────────────────────────────
  analytics
    .command('agents')
    .description('AGI score leaderboard')
    .action(async () => {
      const bundle = await buildBundle();
      const scorer = new AgentScorer();
      if (bundle.agents.length === 0) {
        console.log('\nNo agent execution data found.\n');
        return;
      }
      console.log(scorer.formatLeaderboard(bundle.agents));
    });

  // ── analytics revenue ─────────────────────────────────────────────────────
  analytics
    .command('revenue')
    .description('Show MRR/ARR/ARPU')
    .action(async () => {
      const bundle = await buildBundle();
      const tracker = new RevenueTracker();
      console.log(tracker.formatSummary(bundle.revenue));
    });

  // ── analytics growth ──────────────────────────────────────────────────────
  analytics
    .command('growth')
    .description('Show MoM/WoW growth trends')
    .action(async () => {
      const bundle = await buildBundle();
      const analyzer = new GrowthAnalyzer();
      console.log(analyzer.formatSummary(bundle.growth));
    });

  // ── analytics export ──────────────────────────────────────────────────────
  analytics
    .command('export <outfile>')
    .description('Export full analytics as Markdown report')
    .action(async (outfile: string) => {
      const bundle = await buildBundle();
      const generator = new ReportGenerator();
      const markdown = generator.toMarkdown(bundle);
      await writeFile(outfile, markdown, 'utf-8');
      console.log(`\nAnalytics report exported to ${outfile}\n`);
    });
}
