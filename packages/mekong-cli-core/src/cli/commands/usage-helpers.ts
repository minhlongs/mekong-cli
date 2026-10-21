/**
 * usage-helpers.ts — Metering store factory, tier lookup, CSV serializer, and export/limits actions.
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { writeFile } from 'node:fs/promises';
import { MeteringStore } from '../../metering/store.js';
import { UsageLimiter } from '../../metering/limiter.js';
import type { LicenseTier } from '../../license/types.js';
import type { UsageCategory, UsageEvent } from '../../metering/types.js';

export const DEFAULT_METERING_DIR = join(homedir(), '.mekong', 'metering');

export function getStore(dir?: string): MeteringStore {
  return new MeteringStore(dir ?? DEFAULT_METERING_DIR);
}

export function getTierFromEnv(): LicenseTier {
  const t = process.env['MEKONG_LICENSE_TIER'];
  if (t === 'starter' || t === 'pro' || t === 'enterprise') return t;
  return 'free';
}

export function padRow(col1: string, col2: string, col3: string, col4: string): string {
  return `  ${col1.padEnd(14)}${col2.padStart(8)}  ${col3.padStart(8)}  ${col4.padStart(10)}`;
}

export function csvEscape(value: unknown): string {
  const s = String(value ?? '');
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function eventsToCSV(events: UsageEvent[]): string {
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

export async function runUsageExport(
  outfile: string,
  opts: { dir?: string; from?: string; to?: string },
): Promise<void> {
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
}

export async function runUsageLimits(opts: { dir?: string; tier?: string }): Promise<void> {
  const store = getStore(opts.dir);
  const tier = (opts.tier as LicenseTier | undefined) ?? getTierFromEnv();
  const limiter = new UsageLimiter(store);

  const categories: UsageCategory[] = ['llm_call', 'tool_run', 'sop_run'];
  console.log(`\nUsage Limits — Today  [tier: ${tier}]\n`);
  console.log(padRow('Category', 'Used', 'Limit', 'Remaining'));
  console.log('─'.repeat(52));

  for (const cat of categories) {
    const res = await limiter.checkLimit(cat, tier);
    if (!res.ok) {
      console.error(`  Error: ${res.error.message}`);
      continue;
    }
    const { used, limit, remaining } = res.value;
    console.log(padRow(
      cat.replace('_', ' '),
      String(used),
      limit === -1 ? '∞' : String(limit),
      remaining === Infinity ? '∞' : String(remaining),
    ));
  }
  console.log('');
}
