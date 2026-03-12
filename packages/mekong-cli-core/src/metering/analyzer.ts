/**
 * UsageAnalyzer — aggregate events into summaries, detect overages.
 */
import type { UsageEvent, MeterReading, UsageSummary, BillingPeriod, OverageInfo } from './types.js';
import type { UsageQuota } from '../license/types.js';
import { periodFromDate } from './store.js';

export class UsageAnalyzer {
  /** Aggregate a list of events into per-day MeterReadings */
  aggregate(events: UsageEvent[]): MeterReading[] {
    const byDay = new Map<string, MeterReading>();

    for (const e of events) {
      const date = e.timestamp.slice(0, 10); // YYYY-MM-DD
      if (!byDay.has(date)) {
        byDay.set(date, {
          date,
          llmCalls: 0,
          toolRuns: 0,
          sopRuns: 0,
          totalInputTokens: 0,
          totalOutputTokens: 0,
          totalCostUsd: 0,
        });
      }
      const r = byDay.get(date)!;
      if (e.category === 'llm_call') {
        r.llmCalls++;
        r.totalInputTokens += e.inputTokens ?? 0;
        r.totalOutputTokens += e.outputTokens ?? 0;
        r.totalCostUsd += e.estimatedCost ?? 0;
      } else if (e.category === 'tool_run') {
        r.toolRuns++;
      } else if (e.category === 'sop_run') {
        r.sopRuns++;
      }
    }

    return Array.from(byDay.values()).sort((a, b) => a.date.localeCompare(b.date));
  }

  /** Sum readings into one totals MeterReading */
  totalize(readings: MeterReading[]): MeterReading {
    const totals: MeterReading = {
      date: 'total',
      llmCalls: 0,
      toolRuns: 0,
      sopRuns: 0,
      totalInputTokens: 0,
      totalOutputTokens: 0,
      totalCostUsd: 0,
    };
    for (const r of readings) {
      totals.llmCalls += r.llmCalls;
      totals.toolRuns += r.toolRuns;
      totals.sopRuns += r.sopRuns;
      totals.totalInputTokens += r.totalInputTokens;
      totals.totalOutputTokens += r.totalOutputTokens;
      totals.totalCostUsd += r.totalCostUsd;
    }
    return totals;
  }

  /** Build a full UsageSummary for a period from raw events */
  summarize(events: UsageEvent[], period?: BillingPeriod): UsageSummary {
    const readings = this.aggregate(events);
    const totals = this.totalize(readings);

    // Infer period from first event if not provided
    const resolvedPeriod = period ?? (events.length > 0
      ? periodFromDate(events[0].timestamp)
      : periodFromDate(new Date().toISOString()));

    // By category counts
    const byCategory = {
      llm_call: 0,
      tool_run: 0,
      sop_run: 0,
    };
    for (const e of events) byCategory[e.category]++;

    // Top models
    const modelMap = new Map<string, { calls: number; costUsd: number }>();
    for (const e of events) {
      if (e.category !== 'llm_call' || !e.model) continue;
      const entry = modelMap.get(e.model) ?? { calls: 0, costUsd: 0 };
      entry.calls++;
      entry.costUsd += e.estimatedCost ?? 0;
      modelMap.set(e.model, entry);
    }
    const topModels = Array.from(modelMap.entries())
      .map(([model, v]) => ({ model, calls: v.calls, costUsd: v.costUsd }))
      .sort((a, b) => b.calls - a.calls)
      .slice(0, 5);

    // Top tools
    const toolMap = new Map<string, number>();
    for (const e of events) {
      if ((e.category !== 'tool_run' && e.category !== 'sop_run') || !e.resourceName) continue;
      toolMap.set(e.resourceName, (toolMap.get(e.resourceName) ?? 0) + 1);
    }
    const topTools = Array.from(toolMap.entries())
      .map(([name, runs]) => ({ name, runs }))
      .sort((a, b) => b.runs - a.runs)
      .slice(0, 5);

    return { period: resolvedPeriod, readings, totals, byCategory, topModels, topTools };
  }

  /** Detect overages vs a quota. Returns one OverageInfo per exceeded category. */
  detectOverages(dailyReading: MeterReading, quota: UsageQuota): OverageInfo[] {
    const overages: OverageInfo[] = [];

    const checks: Array<{ key: keyof MeterReading; limit: number; category: 'llm_call' | 'tool_run' | 'sop_run' }> = [
      { key: 'llmCalls', limit: quota.llmCallsPerDay, category: 'llm_call' },
      { key: 'toolRuns', limit: quota.toolRunsPerDay, category: 'tool_run' },
      { key: 'sopRuns', limit: quota.sopRunsPerDay, category: 'sop_run' },
    ];

    for (const { key, limit, category } of checks) {
      if (limit === -1) continue; // unlimited
      const used = dailyReading[key] as number;
      if (used > limit) {
        overages.push({
          category,
          limit,
          used,
          over: used - limit,
          percentUsed: limit > 0 ? Math.round((used / limit) * 100) : 100,
        });
      }
    }

    return overages;
  }

  /** Estimate cost from events using a simple per-token rate */
  estimateCost(events: UsageEvent[]): number {
    return events.reduce((sum, e) => sum + (e.estimatedCost ?? 0), 0);
  }

  /** Get today's reading from a list of events */
  todayReading(events: UsageEvent[]): MeterReading {
    const today = new Date().toISOString().slice(0, 10);
    const todayEvents = events.filter((e) => e.timestamp.startsWith(today));
    const readings = this.aggregate(todayEvents);
    return readings[0] ?? {
      date: today,
      llmCalls: 0,
      toolRuns: 0,
      sopRuns: 0,
      totalInputTokens: 0,
      totalOutputTokens: 0,
      totalCostUsd: 0,
    };
  }
}
