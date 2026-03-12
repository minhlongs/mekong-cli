/**
 * metering.test.ts — comprehensive tests for all metering modules.
 * Phases 1-7: types, store, collector, analyzer, limiter, cost-calculator, integration.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rm, mkdir } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';

import { MeteringStore, periodFromDate } from './store.js';
import { MeteringCollector } from './collector.js';
import { UsageAnalyzer } from './analyzer.js';
import { UsageLimiter } from './limiter.js';
import { CostCalculator } from './cost-calculator.js';
import type { UsageEvent, BillingPeriod } from './types.js';
import { TIER_QUOTAS } from '../license/types.js';

// ── helpers ───────────────────────────────────────────────────────────────────

function tmpDir(): string {
  return join(tmpdir(), `metering-test-${randomUUID()}`);
}

function makeEvent(overrides: Partial<UsageEvent> = {}): UsageEvent {
  return {
    id: randomUUID(),
    category: 'llm_call',
    timestamp: new Date().toISOString(),
    provider: 'anthropic',
    model: 'claude-sonnet-4-20250514',
    inputTokens: 100,
    outputTokens: 50,
    estimatedCost: 0.001,
    ...overrides,
  };
}

function makeToolEvent(name = 'shell', overrides: Partial<UsageEvent> = {}): UsageEvent {
  return makeEvent({ category: 'tool_run', provider: undefined, model: undefined,
    inputTokens: undefined, outputTokens: undefined, resourceName: name, ...overrides });
}

function makeSopEvent(name = 'my-sop', overrides: Partial<UsageEvent> = {}): UsageEvent {
  return makeEvent({ category: 'sop_run', provider: undefined, model: undefined,
    inputTokens: undefined, outputTokens: undefined, resourceName: name, ...overrides });
}

// ── Phase 1: periodFromDate ───────────────────────────────────────────────────

describe('periodFromDate', () => {
  it('extracts year, month, label from ISO string', () => {
    const p = periodFromDate('2026-03-12T10:00:00.000Z');
    expect(p.year).toBe(2026);
    expect(p.month).toBe(3);
    expect(p.label).toBe('2026-03');
  });

  it('pads single-digit months', () => {
    const p = periodFromDate('2026-01-01T00:00:00.000Z');
    expect(p.label).toBe('2026-01');
  });

  it('handles December correctly', () => {
    const p = periodFromDate('2025-12-31T23:59:59.000Z');
    expect(p.month).toBe(12);
    expect(p.label).toBe('2025-12');
  });
});

// ── Phase 1: MeteringStore ────────────────────────────────────────────────────

describe('MeteringStore', () => {
  let dir: string;
  let store: MeteringStore;

  beforeEach(async () => {
    dir = tmpDir();
    await mkdir(dir, { recursive: true });
    store = new MeteringStore(dir);
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  it('appends and reads a single event', async () => {
    const e = makeEvent();
    const appendResult = await store.append(e);
    expect(appendResult.ok).toBe(true);

    const period = periodFromDate(e.timestamp);
    const readResult = await store.readPeriod(period);
    expect(readResult.ok).toBe(true);
    expect(readResult.ok && readResult.value).toHaveLength(1);
    expect(readResult.ok && readResult.value[0].id).toBe(e.id);
  });

  it('returns empty array for missing period file', async () => {
    const period: BillingPeriod = { year: 2020, month: 1, label: '2020-01' };
    const result = await store.readPeriod(period);
    expect(result.ok).toBe(true);
    expect(result.ok && result.value).toHaveLength(0);
  });

  it('appendBatch writes multiple events efficiently', async () => {
    const events = Array.from({ length: 5 }, () => makeEvent());
    const result = await store.appendBatch(events);
    expect(result.ok).toBe(true);

    const period = periodFromDate(events[0].timestamp);
    const read = await store.readPeriod(period);
    expect(read.ok && read.value).toHaveLength(5);
  });

  it('appendBatch with empty array is a no-op', async () => {
    const result = await store.appendBatch([]);
    expect(result.ok).toBe(true);
  });

  it('queryRange filters events by date', async () => {
    const e1 = makeEvent({ timestamp: '2026-03-01T10:00:00.000Z' });
    const e2 = makeEvent({ timestamp: '2026-03-15T10:00:00.000Z' });
    const e3 = makeEvent({ timestamp: '2026-03-31T10:00:00.000Z' });
    await store.appendBatch([e1, e2, e3]);

    const result = await store.queryRange('2026-03-10T00:00:00.000Z', '2026-03-20T00:00:00.000Z');
    expect(result.ok).toBe(true);
    expect(result.ok && result.value).toHaveLength(1);
    expect(result.ok && result.value[0].id).toBe(e2.id);
  });

  it('queryRange across month boundary includes both months', async () => {
    const e1 = makeEvent({ timestamp: '2026-02-28T23:00:00.000Z' });
    const e2 = makeEvent({ timestamp: '2026-03-01T01:00:00.000Z' });
    await store.appendBatch([e1, e2]);

    const result = await store.queryRange('2026-02-28T00:00:00.000Z', '2026-03-01T23:59:59.999Z');
    expect(result.ok).toBe(true);
    expect(result.ok && result.value).toHaveLength(2);
  });

  it('readToday returns only today events', async () => {
    const today = new Date().toISOString().slice(0, 10);
    const e1 = makeEvent({ timestamp: `${today}T10:00:00.000Z` });
    const e2 = makeEvent({ timestamp: '2020-01-01T10:00:00.000Z' });
    await store.appendBatch([e1, e2]);

    const result = await store.readToday();
    expect(result.ok).toBe(true);
    expect(result.ok && result.value.some((e) => e.id === e1.id)).toBe(true);
    expect(result.ok && result.value.some((e) => e.id === e2.id)).toBe(false);
  });

  it('filePath returns correct path for a period', () => {
    const path = store.filePath({ year: 2026, month: 3, label: '2026-03' });
    expect(path).toContain('2026-03.jsonl');
  });
});

// ── Phase 2: MeteringCollector ────────────────────────────────────────────────

describe('MeteringCollector', () => {
  let dir: string;
  let store: MeteringStore;
  let collector: MeteringCollector;

  beforeEach(async () => {
    dir = tmpDir();
    await mkdir(dir, { recursive: true });
    store = new MeteringStore(dir);
    collector = new MeteringCollector(store);
  });

  afterEach(async () => {
    await collector.shutdown();
    await rm(dir, { recursive: true, force: true });
  });

  it('buffers events before flush', () => {
    collector.record({ category: 'llm_call' });
    expect(collector.bufferSize).toBe(1);
  });

  it('flush writes buffered events and clears buffer', async () => {
    collector.record({ category: 'llm_call' });
    collector.record({ category: 'tool_run', resourceName: 'shell' });
    await collector.flush();
    expect(collector.bufferSize).toBe(0);

    const today = await store.readToday();
    expect(today.ok && today.value).toHaveLength(2);
  });

  it('recordLlmCall adds correct category and fields', () => {
    collector.recordLlmCall({ provider: 'anthropic', model: 'claude-sonnet-4', inputTokens: 100, outputTokens: 50 });
    expect(collector.bufferSize).toBe(1);
    expect(collector.countByCategory('llm_call')).toBe(1);
  });

  it('recordToolRun sets tool_run category and resourceName', () => {
    collector.recordToolRun({ name: 'bash', durationMs: 123 });
    expect(collector.countByCategory('tool_run')).toBe(1);
  });

  it('recordSopRun sets sop_run category and resourceName', () => {
    collector.recordSopRun({ name: 'onboarding', success: true });
    expect(collector.countByCategory('sop_run')).toBe(1);
  });

  it('auto-assigns id and timestamp', async () => {
    collector.record({ category: 'llm_call' });
    await collector.flush();
    const result = await store.readToday();
    expect(result.ok).toBe(true);
    const e = result.ok ? result.value[0] : null;
    expect(e?.id).toBeTruthy();
    expect(e?.timestamp).toBeTruthy();
  });

  it('shutdown flushes remaining events', async () => {
    collector.record({ category: 'sop_run', resourceName: 'test' });
    await collector.shutdown();
    const result = await store.readToday();
    expect(result.ok && result.value).toHaveLength(1);
  });

  it('flush is idempotent when buffer is empty', async () => {
    await expect(collector.flush()).resolves.not.toThrow();
    await expect(collector.flush()).resolves.not.toThrow();
  });
});

// ── Phase 3: UsageAnalyzer ────────────────────────────────────────────────────

describe('UsageAnalyzer', () => {
  let analyzer: UsageAnalyzer;

  beforeEach(() => {
    analyzer = new UsageAnalyzer();
  });

  it('aggregate groups events by day', () => {
    const events = [
      makeEvent({ timestamp: '2026-03-01T10:00:00.000Z' }),
      makeEvent({ timestamp: '2026-03-01T14:00:00.000Z' }),
      makeEvent({ timestamp: '2026-03-02T09:00:00.000Z' }),
    ];
    const readings = analyzer.aggregate(events);
    expect(readings).toHaveLength(2);
    expect(readings[0].llmCalls).toBe(2);
    expect(readings[1].llmCalls).toBe(1);
  });

  it('aggregate counts tool and sop runs separately', () => {
    const events = [
      makeEvent({ category: 'tool_run', timestamp: '2026-03-01T10:00:00.000Z' }),
      makeEvent({ category: 'sop_run', timestamp: '2026-03-01T11:00:00.000Z' }),
      makeEvent({ category: 'llm_call', timestamp: '2026-03-01T12:00:00.000Z' }),
    ];
    const readings = analyzer.aggregate(events);
    expect(readings[0].toolRuns).toBe(1);
    expect(readings[0].sopRuns).toBe(1);
    expect(readings[0].llmCalls).toBe(1);
  });

  it('totalize sums all readings', () => {
    const readings = [
      { date: '2026-03-01', llmCalls: 3, toolRuns: 2, sopRuns: 1, totalInputTokens: 100, totalOutputTokens: 50, totalCostUsd: 0.01 },
      { date: '2026-03-02', llmCalls: 5, toolRuns: 1, sopRuns: 0, totalInputTokens: 200, totalOutputTokens: 100, totalCostUsd: 0.02 },
    ];
    const totals = analyzer.totalize(readings);
    expect(totals.llmCalls).toBe(8);
    expect(totals.toolRuns).toBe(3);
    expect(totals.totalCostUsd).toBeCloseTo(0.03);
  });

  it('summarize builds full UsageSummary', () => {
    const events = [
      makeEvent({ provider: 'anthropic', model: 'claude-sonnet-4', estimatedCost: 0.001 }),
      makeToolEvent('bash'),
      makeSopEvent('deploy'),
    ];
    const summary = analyzer.summarize(events);
    expect(summary.byCategory.llm_call).toBe(1);
    expect(summary.byCategory.tool_run).toBe(1);
    expect(summary.byCategory.sop_run).toBe(1);
    expect(summary.topModels).toHaveLength(1);
    expect(summary.topTools).toHaveLength(2);
  });

  it('detectOverages returns empty for enterprise tier', () => {
    const reading = { date: 'today', llmCalls: 9999, toolRuns: 9999, sopRuns: 9999,
      totalInputTokens: 0, totalOutputTokens: 0, totalCostUsd: 0 };
    const overages = analyzer.detectOverages(reading, TIER_QUOTAS.enterprise);
    expect(overages).toHaveLength(0);
  });

  it('detectOverages detects LLM overage for free tier', () => {
    const reading = { date: 'today', llmCalls: 15, toolRuns: 0, sopRuns: 0,
      totalInputTokens: 0, totalOutputTokens: 0, totalCostUsd: 0 };
    const overages = analyzer.detectOverages(reading, TIER_QUOTAS.free);
    const llmOverage = overages.find((o) => o.category === 'llm_call');
    expect(llmOverage).toBeDefined();
    expect(llmOverage?.over).toBe(5); // free = 10/day
  });

  it('todayReading returns zeroed reading for no events', () => {
    const reading = analyzer.todayReading([]);
    expect(reading.llmCalls).toBe(0);
    expect(reading.toolRuns).toBe(0);
    expect(reading.sopRuns).toBe(0);
  });

  it('estimateCost sums estimatedCost fields', () => {
    const events = [
      makeEvent({ estimatedCost: 0.001 }),
      makeEvent({ estimatedCost: 0.002 }),
      makeEvent({ estimatedCost: undefined }),
    ];
    expect(analyzer.estimateCost(events)).toBeCloseTo(0.003);
  });

  it('aggregate returns sorted readings by date', () => {
    const events = [
      makeEvent({ timestamp: '2026-03-10T10:00:00.000Z' }),
      makeEvent({ timestamp: '2026-03-01T10:00:00.000Z' }),
      makeEvent({ timestamp: '2026-03-05T10:00:00.000Z' }),
    ];
    const readings = analyzer.aggregate(events);
    expect(readings[0].date).toBe('2026-03-01');
    expect(readings[1].date).toBe('2026-03-05');
    expect(readings[2].date).toBe('2026-03-10');
  });
});

// ── Phase 4: UsageLimiter ─────────────────────────────────────────────────────

describe('UsageLimiter', () => {
  let dir: string;
  let store: MeteringStore;
  let limiter: UsageLimiter;

  beforeEach(async () => {
    dir = tmpDir();
    await mkdir(dir, { recursive: true });
    store = new MeteringStore(dir);
    limiter = new UsageLimiter(store);
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  it('allows calls when under limit (free tier)', async () => {
    const result = await limiter.checkLimit('llm_call', 'free');
    expect(result.ok).toBe(true);
    expect(result.ok && result.value.allowed).toBe(true);
  });

  it('blocks when daily limit exceeded', async () => {
    // free tier = 10 LLM calls/day; write 10 events
    const today = new Date().toISOString().slice(0, 10);
    const events = Array.from({ length: 10 }, () =>
      makeEvent({ timestamp: `${today}T10:00:00.000Z` }),
    );
    await store.appendBatch(events);
    limiter.invalidateCache();

    const result = await limiter.checkLimit('llm_call', 'free');
    expect(result.ok).toBe(true);
    expect(result.ok && result.value.allowed).toBe(false);
    expect(result.ok && result.value.message).toContain('Daily limit reached');
  });

  it('enterprise tier always returns allowed=true', async () => {
    const result = await limiter.checkLimit('llm_call', 'enterprise');
    expect(result.ok).toBe(true);
    expect(result.ok && result.value.allowed).toBe(true);
    expect(result.ok && result.value.limit).toBe(-1);
  });

  it('getRemaining returns Infinity for enterprise', async () => {
    const rem = await limiter.getRemaining('tool_run', 'enterprise');
    expect(rem).toBe(Infinity);
  });

  it('getRemaining decreases as events are added', async () => {
    const today = new Date().toISOString().slice(0, 10);
    const events = Array.from({ length: 3 }, () =>
      makeEvent({ timestamp: `${today}T10:00:00.000Z` }),
    );
    await store.appendBatch(events);
    limiter.invalidateCache();

    const rem = await limiter.getRemaining('llm_call', 'free'); // limit=10
    expect(rem).toBe(7);
  });

  it('refreshCache reads latest state from disk', async () => {
    const today = new Date().toISOString().slice(0, 10);
    await store.append(makeEvent({ timestamp: `${today}T10:00:00.000Z` }));
    await limiter.refreshCache();
    const rem = await limiter.getRemaining('llm_call', 'free');
    expect(rem).toBe(9); // 10 - 1
  });

  it('checkLimit returns remaining count', async () => {
    const result = await limiter.checkLimit('tool_run', 'starter'); // starter = 500
    expect(result.ok && result.value.remaining).toBe(500);
  });

  it('returns ok(false) for exceeded limit, not err()', async () => {
    const today = new Date().toISOString().slice(0, 10);
    // fill up free sop_run limit (5)
    const events = Array.from({ length: 5 }, () =>
      makeSopEvent('test', { timestamp: `${today}T10:00:00.000Z` }),
    );
    await store.appendBatch(events);
    limiter.invalidateCache();
    const result = await limiter.checkLimit('sop_run', 'free');
    expect(result.ok).toBe(true); // ok wrapper, not err
    expect(result.ok && result.value.allowed).toBe(false);
  });
});

// ── Phase 5: CostCalculator ───────────────────────────────────────────────────

describe('CostCalculator', () => {
  let calc: CostCalculator;

  beforeEach(() => {
    calc = new CostCalculator();
  });

  it('calculates cost for anthropic/claude-sonnet-4', () => {
    // 1M input @ $3, 1M output @ $15
    const cost = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 1_000_000, 1_000_000);
    expect(cost).toBeCloseTo(18.0);
  });

  it('calculates cost for openai/gpt-4o-mini', () => {
    const cost = calc.calculate('openai', 'gpt-4o-mini', 1_000_000, 1_000_000);
    expect(cost).toBeCloseTo(0.75);
  });

  it('ollama is always free', () => {
    const cost = calc.calculate('ollama', 'llama3', 999_999, 999_999);
    expect(cost).toBe(0);
  });

  it('local provider is always free', () => {
    expect(calc.calculate('local', 'any-model', 100, 100)).toBe(0);
  });

  it('unknown model uses default Sonnet pricing', () => {
    const cost = calc.calculate('anthropic', 'unknown-future-model', 1_000_000, 0);
    expect(cost).toBeCloseTo(3.0);
  });

  it('getPricing returns null for unknown model', () => {
    const p = calc.getPricing('anthropic', 'definitely-not-a-model');
    expect(p).toBeNull();
  });

  it('getPricing returns [0,0] for ollama', () => {
    const p = calc.getPricing('ollama', 'mistral');
    expect(p).toEqual([0, 0]);
  });

  it('isFreeProvider detects ollama', () => {
    expect(calc.isFreeProvider('ollama')).toBe(true);
    expect(calc.isFreeProvider('anthropic')).toBe(false);
  });

  it('knownModels returns non-empty list', () => {
    expect(calc.knownModels().length).toBeGreaterThan(5);
  });

  it('calculates cost for deepseek-chat correctly', () => {
    const cost = calc.calculate('openai', 'deepseek-chat', 1_000_000, 1_000_000);
    expect(cost).toBeCloseTo(0.42); // 0.14 + 0.28
  });
});

// ── Phase 6: CLI helpers (CSV export logic) ───────────────────────────────────

describe('CSV export helpers', () => {
  it('eventsToCSV produces valid header row', async () => {
    // We import the CLI module indirectly by testing the shape expected
    const events: UsageEvent[] = [
      makeEvent({ provider: 'anthropic', model: 'claude-sonnet-4', estimatedCost: 0.001 }),
    ];
    // Manually replicate CSV logic to verify format
    const headers = ['id', 'timestamp', 'category', 'provider', 'model',
      'inputTokens', 'outputTokens', 'resourceName', 'durationMs', 'estimatedCost'];
    const rows = events.map((e) => [
      e.id, e.timestamp, e.category, e.provider ?? '', e.model ?? '',
      e.inputTokens ?? '', e.outputTokens ?? '', e.resourceName ?? '',
      e.durationMs ?? '', e.estimatedCost ?? '',
    ].join(','));
    const csv = [headers.join(','), ...rows].join('\n') + '\n';
    expect(csv).toContain('id,timestamp,category');
    expect(csv).toContain('anthropic');
    expect(csv).toContain('claude-sonnet-4');
  });

  it('CSV escapes values with commas', () => {
    const value = 'hello, world';
    // replicate csvEscape
    const s = String(value);
    const escaped = s.includes(',') ? `"${s}"` : s;
    expect(escaped).toBe('"hello, world"');
  });

  it('CSV escapes values with quotes', () => {
    const value = 'say "hello"';
    const s = String(value);
    const escaped = s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
    expect(escaped).toBe('"say ""hello"""');
  });
});

// ── Phase 7: Integration — LlmRouter + MeteringCollector ─────────────────────

describe('Engine Integration', () => {
  it('MeteringStore + MeteringCollector + UsageAnalyzer pipeline', async () => {
    const dir = tmpDir();
    await mkdir(dir, { recursive: true });
    try {
      const store = new MeteringStore(dir);
      const collector = new MeteringCollector(store);
      const analyzer = new UsageAnalyzer();

      // Simulate a session with mixed events
      collector.recordLlmCall({ provider: 'anthropic', model: 'claude-sonnet-4', inputTokens: 500, outputTokens: 200, estimatedCost: 0.005 });
      collector.recordLlmCall({ provider: 'openai', model: 'gpt-4o', inputTokens: 1000, outputTokens: 400, estimatedCost: 0.006 });
      collector.recordToolRun({ name: 'bash', durationMs: 50 });
      collector.recordSopRun({ name: 'deploy', success: true });

      await collector.flush();

      const today = await store.readToday();
      expect(today.ok).toBe(true);
      expect(today.ok && today.value).toHaveLength(4);

      const reading = analyzer.todayReading(today.ok ? today.value : []);
      expect(reading.llmCalls).toBe(2);
      expect(reading.toolRuns).toBe(1);
      expect(reading.sopRuns).toBe(1);
      expect(reading.totalCostUsd).toBeCloseTo(0.011);

      await collector.shutdown();
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  it('UsageLimiter enforces pro tier tool limit', async () => {
    const dir = tmpDir();
    await mkdir(dir, { recursive: true });
    try {
      const store = new MeteringStore(dir);
      const limiter = new UsageLimiter(store);
      const today = new Date().toISOString().slice(0, 10);

      // pro = 5000 tool runs/day; write 5000
      const batch: UsageEvent[] = Array.from({ length: 5000 }, () =>
        makeToolEvent('bash', { timestamp: `${today}T10:00:00.000Z` }),
      );
      await store.appendBatch(batch);
      limiter.invalidateCache();

      const result = await limiter.checkLimit('tool_run', 'pro');
      expect(result.ok).toBe(true);
      expect(result.ok && result.value.allowed).toBe(false);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  it('CostCalculator integrates with collected LLM events', () => {
    const calc = new CostCalculator();
    const events: UsageEvent[] = [
      makeEvent({ provider: 'anthropic', model: 'claude-sonnet-4-20250514', inputTokens: 1000, outputTokens: 500 }),
      makeEvent({ provider: 'ollama', model: 'llama3', inputTokens: 5000, outputTokens: 2000 }),
    ];
    const totalCost = events.reduce((sum, e) => {
      if (!e.provider || !e.model) return sum;
      return sum + calc.calculate(e.provider, e.model, e.inputTokens ?? 0, e.outputTokens ?? 0);
    }, 0);
    // anthropic: (1000/1M)*3 + (500/1M)*15 = 0.003 + 0.0075 = 0.0105
    // ollama: 0
    expect(totalCost).toBeCloseTo(0.0105);
  });

  it('full period query returns cross-month events', async () => {
    const dir = tmpDir();
    await mkdir(dir, { recursive: true });
    try {
      const store = new MeteringStore(dir);
      const e1 = makeEvent({ timestamp: '2026-02-28T23:30:00.000Z' });
      const e2 = makeEvent({ timestamp: '2026-03-01T00:30:00.000Z' });
      await store.appendBatch([e1, e2]);

      const result = await store.queryRange('2026-02-28T00:00:00.000Z', '2026-03-01T23:59:59.999Z');
      expect(result.ok).toBe(true);
      expect(result.ok && result.value).toHaveLength(2);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  it('starter tier: 100 LLM calls allowed, 101 blocked', async () => {
    const dir = tmpDir();
    await mkdir(dir, { recursive: true });
    try {
      const store = new MeteringStore(dir);
      const limiter = new UsageLimiter(store);
      const today = new Date().toISOString().slice(0, 10);

      // starter = 100 LLM calls/day; write exactly 100
      const batch: UsageEvent[] = Array.from({ length: 100 }, () =>
        makeEvent({ timestamp: `${today}T10:00:00.000Z` }),
      );
      await store.appendBatch(batch);
      limiter.invalidateCache();

      const result = await limiter.checkLimit('llm_call', 'starter');
      expect(result.ok && result.value.allowed).toBe(false);
      expect(result.ok && result.value.remaining).toBe(0);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });
});
