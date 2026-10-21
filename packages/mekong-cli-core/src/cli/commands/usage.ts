/**
 * `mekong usage` — Usage metering subcommands.
 *
 *   mekong usage summary        Overall summary (current month)
 *   mekong usage today          Today's usage table by category
 *   mekong usage this-month     Monthly aggregate with cost
 *   mekong usage export <file>  Export events as CSV
 *   mekong usage limits         Show tier quotas and remaining
 */
import type { Command } from 'commander';
import { periodFromDate } from '../../metering/store.js';
import { UsageAnalyzer } from '../../metering/analyzer.js';
import { TIER_QUOTAS } from '../../license/types.js';
import {
  getStore,
  getTierFromEnv,
  padRow,
  runUsageExport,
  runUsageLimits,
} from './usage-helpers.js';

export function registerUsageCommand(program: Command): void {
  const usage = program
    .command('usage')
    .description('Usage metering — track LLM calls, tool runs, SOP executions');

  // ── usage today ─────────────────────────────────────────────────────────────
  usage
    .command('today')
    .description('Show today\'s usage by category')
    .option('--dir <path>', 'Custom metering directory')
    .action(async (opts: { dir?: string }) => {
      const store = getStore(opts.dir);
      const analyzer = new UsageAnalyzer();
      const result = await store.readToday();
      if (!result.ok) {
        console.error('Error reading usage:', result.error.message);
        process.exit(1);
      }
      const reading = analyzer.todayReading(result.value);
      const tier = getTierFromEnv();
      const quota = TIER_QUOTAS[tier];

      console.log(`\nUsage — Today (${reading.date})  [tier: ${tier}]\n`);
      console.log(padRow('Category', 'Used', 'Limit', 'Remaining'));
      console.log('─'.repeat(52));
      console.log(padRow(
        'LLM Calls',
        String(reading.llmCalls),
        quota.llmCallsPerDay === -1 ? '∞' : String(quota.llmCallsPerDay),
        quota.llmCallsPerDay === -1 ? '∞' : String(Math.max(0, quota.llmCallsPerDay - reading.llmCalls)),
      ));
      console.log(padRow(
        'Tool Runs',
        String(reading.toolRuns),
        quota.toolRunsPerDay === -1 ? '∞' : String(quota.toolRunsPerDay),
        quota.toolRunsPerDay === -1 ? '∞' : String(Math.max(0, quota.toolRunsPerDay - reading.toolRuns)),
      ));
      console.log(padRow(
        'SOP Runs',
        String(reading.sopRuns),
        quota.sopRunsPerDay === -1 ? '∞' : String(quota.sopRunsPerDay),
        quota.sopRunsPerDay === -1 ? '∞' : String(Math.max(0, quota.sopRunsPerDay - reading.sopRuns)),
      ));
      console.log('─'.repeat(52));
      console.log(`  Cost (est): $${reading.totalCostUsd.toFixed(6)}\n`);
    });

  // ── usage this-month ─────────────────────────────────────────────────────────
  usage
    .command('this-month')
    .description('Show this month\'s aggregate usage with cost')
    .option('--dir <path>', 'Custom metering directory')
    .action(async (opts: { dir?: string }) => {
      const store = getStore(opts.dir);
      const analyzer = new UsageAnalyzer();
      const period = periodFromDate(new Date().toISOString());
      const result = await store.readPeriod(period);
      if (!result.ok) {
        console.error('Error reading usage:', result.error.message);
        process.exit(1);
      }
      const summary = analyzer.summarize(result.value, period);
      const { totals } = summary;

      console.log(`\nUsage — ${period.label}\n`);
      console.log(`  LLM Calls  : ${totals.llmCalls}`);
      console.log(`  Tool Runs  : ${totals.toolRuns}`);
      console.log(`  SOP Runs   : ${totals.sopRuns}`);
      console.log(`  Input Tok  : ${totals.totalInputTokens.toLocaleString()}`);
      console.log(`  Output Tok : ${totals.totalOutputTokens.toLocaleString()}`);
      console.log(`  Cost (est) : $${totals.totalCostUsd.toFixed(6)}`);

      if (summary.topModels.length > 0) {
        console.log('\n  Top Models:');
        for (const m of summary.topModels) {
          console.log(`    ${m.model.padEnd(36)} ${String(m.calls).padStart(5)} calls  $${m.costUsd.toFixed(6)}`);
        }
      }
      console.log('');
    });

  // ── usage summary ────────────────────────────────────────────────────────────
  usage
    .command('summary')
    .description('Overall usage summary for current month')
    .option('--dir <path>', 'Custom metering directory')
    .action(async (opts: { dir?: string }) => {
      const store = getStore(opts.dir);
      const analyzer = new UsageAnalyzer();
      const period = periodFromDate(new Date().toISOString());
      const result = await store.readPeriod(period);
      if (!result.ok) {
        console.error('Error reading usage:', result.error.message);
        process.exit(1);
      }
      const summary = analyzer.summarize(result.value, period);
      const { totals, byCategory } = summary;
      const total = Object.values(byCategory).reduce((a, b) => a + b, 0);

      console.log(`\nUsage Summary — ${period.label}\n`);
      console.log(`  Total events : ${total}`);
      console.log(`    llm_call   : ${byCategory.llm_call}`);
      console.log(`    tool_run   : ${byCategory.tool_run}`);
      console.log(`    sop_run    : ${byCategory.sop_run}`);
      console.log(`  Est. cost    : $${totals.totalCostUsd.toFixed(6)}`);
      console.log(`  Days tracked : ${summary.readings.length}`);
      console.log('');
    });

  // ── usage export ─────────────────────────────────────────────────────────────
  usage
    .command('export <outfile>')
    .description('Export usage events as CSV')
    .option('--dir <path>', 'Custom metering directory')
    .option('--from <date>', 'Start date YYYY-MM-DD (default: start of month)')
    .option('--to <date>', 'End date YYYY-MM-DD (default: today)')
    .action(runUsageExport);

  // ── usage limits ─────────────────────────────────────────────────────────────
  usage
    .command('limits')
    .description('Show tier quotas and remaining allowances for today')
    .option('--dir <path>', 'Custom metering directory')
    .option('--tier <tier>', 'Override tier (free|starter|pro|enterprise)')
    .action(runUsageLimits);
}
