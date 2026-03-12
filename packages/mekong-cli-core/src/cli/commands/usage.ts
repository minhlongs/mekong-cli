/**
 * `mekong usage` — Usage metering subcommands.
 *
 *   mekong usage summary        Overall summary (current month)
 *   mekong usage today          Today's usage table by category
 *   mekong usage this-month     Monthly aggregate with cost
 *   mekong usage export <file>  Export events as CSV
 *   mekong usage limits         Show tier quotas and remaining
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { writeFile } from 'node:fs/promises';
import type { Command } from 'commander';
import { MeteringStore, periodFromDate } from '../../metering/store.js';
import { UsageAnalyzer } from '../../metering/analyzer.js';
import { UsageLimiter } from '../../metering/limiter.js';
import { TIER_QUOTAS } from '../../license/types.js';
import type { LicenseTier } from '../../license/types.js';
import type { UsageCategory } from '../../metering/types.js';

const DEFAULT_METERING_DIR = join(homedir(), '.mekong', 'metering');

function getStore(dir?: string): MeteringStore {
  return new MeteringStore(dir ?? DEFAULT_METERING_DIR);
}

function getTierFromEnv(): LicenseTier {
  const t = process.env['MEKONG_LICENSE_TIER'];
  if (t === 'starter' || t === 'pro' || t === 'enterprise') return t;
  return 'free';
}

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
      console.log(
        padRow('Category', 'Used', 'Limit', 'Remaining'),
      );
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
    .action(async (outfile: string, opts: { dir?: string; from?: string; to?: string }) => {
      const store = getStore(opts.dir);
      const now = new Date();
      const monthStart = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-01T00:00:00.000Z`;
      const dayEnd = `${now.toISOString().slice(0, 10)}T23:59:59.999Z`;

      const from = opts.from ? `${opts.from}T00:00:00.000Z` : monthStart;
      const to = opts.to ? `${opts.to}T23:59:59.999Z` : dayEnd;

      const result = await store.queryRange(from, to);
      if (!result.ok) {
        console.error('Error reading usage:', result.error.message);
        process.exit(1);
      }

      const csv = eventsToCSV(result.value);
      await writeFile(outfile, csv, 'utf-8');
      console.log(`\nExported ${result.value.length} events to ${outfile}\n`);
    });

  // ── usage limits ─────────────────────────────────────────────────────────────
  usage
    .command('limits')
    .description('Show tier quotas and remaining allowances for today')
    .option('--dir <path>', 'Custom metering directory')
    .option('--tier <tier>', 'Override tier (free|starter|pro|enterprise)')
    .action(async (opts: { dir?: string; tier?: string }) => {
      const store = getStore(opts.dir);
      const tier = (opts.tier as LicenseTier | undefined) ?? getTierFromEnv();
      const limiter = new UsageLimiter(store);

      const categories: UsageCategory[] = ['llm_call', 'tool_run', 'sop_run'];
      console.log(`\nUsage Limits — Today  [tier: ${tier}]\n`);
      console.log(padRow('Category', 'Used', 'Limit', 'Remaining'));
      console.log('─'.repeat(52));

      for (const cat of categories) {
        const res = await limiter.checkLimit(cat, tier);
        if (!res.ok) { console.error(`  Error: ${res.error.message}`); continue; }
        const { used, limit, remaining } = res.value;
        console.log(padRow(
          cat.replace('_', ' '),
          String(used),
          limit === -1 ? '∞' : String(limit),
          remaining === Infinity ? '∞' : String(remaining),
        ));
      }
      console.log('');
    });
}

// ── helpers ───────────────────────────────────────────────────────────────────

function padRow(col1: string, col2: string, col3: string, col4: string): string {
  return `  ${col1.padEnd(14)}${col2.padStart(8)}  ${col3.padStart(8)}  ${col4.padStart(10)}`;
}

function eventsToCSV(events: import('../../metering/types.js').UsageEvent[]): string {
  const headers = ['id', 'timestamp', 'category', 'provider', 'model',
    'inputTokens', 'outputTokens', 'resourceName', 'durationMs', 'estimatedCost'];
  const rows = events.map((e) => [
    e.id,
    e.timestamp,
    e.category,
    e.provider ?? '',
    e.model ?? '',
    e.inputTokens ?? '',
    e.outputTokens ?? '',
    e.resourceName ?? '',
    e.durationMs ?? '',
    e.estimatedCost ?? '',
  ].map(csvEscape).join(','));
  return [headers.join(','), ...rows].join('\n') + '\n';
}

function csvEscape(value: unknown): string {
  const s = String(value ?? '');
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}
