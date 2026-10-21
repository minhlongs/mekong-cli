/**
 * `mekong analytics` — ROI Analytics subcommands (v0.8).
 *
 *   mekong analytics roi              ROI % with breakdown
 *   mekong analytics agents           AGI score leaderboard
 *   mekong analytics revenue          MRR/ARR/ARPU
 *   mekong analytics growth           MoM/WoW growth trends
 *   mekong analytics export <file>    Full Markdown report
 */
import { writeFile } from 'node:fs/promises';
import type { Command } from 'commander';
import { AgentScorer } from '../../analytics/agent-scorer.js';
import { RevenueTracker } from '../../analytics/revenue-tracker.js';
import { GrowthAnalyzer } from '../../analytics/growth-analyzer.js';
import { ReportGenerator } from '../../analytics/report-generator.js';
import { HOURLY_RATE, buildBundle } from './analytics-bundle.js';

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
