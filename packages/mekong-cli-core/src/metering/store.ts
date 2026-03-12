/**
 * MeteringStore — JSONL append-only storage for usage events.
 * Monthly rotation: ~/.mekong/metering/YYYY-MM.jsonl
 */
import { appendFile, readFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { homedir } from 'node:os';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { UsageEvent, BillingPeriod } from './types.js';

export class MeteringStore {
  private readonly dir: string;

  constructor(dir?: string) {
    this.dir = dir ?? join(homedir(), '.mekong', 'metering');
  }

  /** Path for a given month */
  filePath(period: BillingPeriod): string {
    return join(this.dir, `${period.label}.jsonl`);
  }

  /** Append a single event to the current month's file */
  async append(event: UsageEvent): Promise<Result<void, Error>> {
    try {
      const period = periodFromDate(event.timestamp);
      const path = this.filePath(period);
      await mkdir(this.dir, { recursive: true });
      await appendFile(path, JSON.stringify(event) + '\n');
      return ok(undefined);
    } catch (e) {
      return err(new Error(`MeteringStore.append failed: ${String(e)}`));
    }
  }

  /** Append multiple events in one pass */
  async appendBatch(events: UsageEvent[]): Promise<Result<void, Error>> {
    if (events.length === 0) return ok(undefined);
    try {
      await mkdir(this.dir, { recursive: true });
      // Group by period to minimise open calls
      const groups = new Map<string, UsageEvent[]>();
      for (const e of events) {
        const p = periodFromDate(e.timestamp);
        const list = groups.get(p.label) ?? [];
        list.push(e);
        groups.set(p.label, list);
      }
      for (const [label, batch] of groups) {
        const path = join(this.dir, `${label}.jsonl`);
        const lines = batch.map((e) => JSON.stringify(e)).join('\n') + '\n';
        await appendFile(path, lines);
      }
      return ok(undefined);
    } catch (e) {
      return err(new Error(`MeteringStore.appendBatch failed: ${String(e)}`));
    }
  }

  /** Read all events for a billing period */
  async readPeriod(period: BillingPeriod): Promise<Result<UsageEvent[], Error>> {
    const path = this.filePath(period);
    return this.readFile(path);
  }

  /** Read events within an ISO date range (inclusive) */
  async queryRange(from: string, to: string): Promise<Result<UsageEvent[], Error>> {
    try {
      const fromMs = new Date(from).getTime();
      const toMs = new Date(to).getTime();
      const fromPeriod = periodFromDate(from);
      const toPeriod = periodFromDate(to);

      // Collect all months in range
      const periods = monthsInRange(fromPeriod, toPeriod);
      const allEvents: UsageEvent[] = [];

      for (const p of periods) {
        const result = await this.readPeriod(p);
        if (!result.ok) continue; // skip missing month files
        allEvents.push(...result.value);
      }

      const filtered = allEvents.filter((e) => {
        const t = new Date(e.timestamp).getTime();
        return t >= fromMs && t <= toMs;
      });

      return ok(filtered);
    } catch (e) {
      return err(new Error(`MeteringStore.queryRange failed: ${String(e)}`));
    }
  }

  /** Read all events for today (UTC) */
  async readToday(): Promise<Result<UsageEvent[], Error>> {
    const now = new Date();
    const todayStr = now.toISOString().slice(0, 10); // YYYY-MM-DD
    const start = `${todayStr}T00:00:00.000Z`;
    const end = `${todayStr}T23:59:59.999Z`;
    return this.queryRange(start, end);
  }

  private async readFile(path: string): Promise<Result<UsageEvent[], Error>> {
    try {
      const content = await readFile(path, 'utf-8');
      const events: UsageEvent[] = [];
      let start = 0;
      const len = content.length;
      for (let i = 0; i <= len; i++) {
        if (i === len || content[i] === '\n') {
          if (i > start) {
            const line = content.slice(start, i);
            if (line.length > 0 && line.charCodeAt(0) !== 32) {
              events.push(JSON.parse(line) as UsageEvent);
            }
          }
          start = i + 1;
        }
      }
      return ok(events);
    } catch (e: unknown) {
      if ((e as NodeJS.ErrnoException).code === 'ENOENT') return ok([]);
      return err(new Error(`MeteringStore.readFile failed: ${String(e)}`));
    }
  }
}

/** Extract BillingPeriod from an ISO timestamp */
export function periodFromDate(isoDate: string): BillingPeriod {
  const d = new Date(isoDate);
  const year = d.getUTCFullYear();
  const month = d.getUTCMonth() + 1;
  const label = `${year}-${String(month).padStart(2, '0')}`;
  return { year, month, label };
}

/** Enumerate all months between two billing periods (inclusive) */
function monthsInRange(from: BillingPeriod, to: BillingPeriod): BillingPeriod[] {
  const result: BillingPeriod[] = [];
  let y = from.year;
  let m = from.month;
  while (y < to.year || (y === to.year && m <= to.month)) {
    const label = `${y}-${String(m).padStart(2, '0')}`;
    result.push({ year: y, month: m, label });
    m++;
    if (m > 12) { m = 1; y++; }
  }
  return result;
}
