/**
 * coverage-gaps-cli.test.ts — tests for untested CLI command output formatting,
 * ReceiptStore error/query paths, MeteringStore edge cases, and UsageAnalyzer paths.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtemp, rm, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';

// ─── ReceiptStore — query paths ───────────────────────────────────────────────

describe('ReceiptStore — query paths', () => {
  let dir: string;
  let storePath: string;

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'receipt-'));
    storePath = join(dir, 'receipts.jsonl');
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  function makeEvent(overrides: Record<string, unknown> = {}) {
    return {
      id: randomUUID(),
      type: 'checkout.completed' as const,
      customerId: 'cust_001',
      customerEmail: 'test@example.com',
      receivedAt: new Date().toISOString(),
      processed: true,
      tier: 'starter',
      ...overrides,
    };
  }

  it('readAll returns empty array when file does not exist', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const result = await store.readAll();
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toEqual([]);
  });

  it('append then readAll round-trips event', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const evt = makeEvent() as import('../payments/types.js').WebhookEvent;
    await store.append(evt);
    const result = await store.readAll();
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.length).toBe(1);
      expect(result.value[0].id).toBe(evt.id);
    }
  });

  it('hasEvent returns false when event not stored', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    expect(await store.hasEvent('nonexistent-id')).toBe(false);
  });

  it('hasEvent returns true after event appended', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const evt = makeEvent() as import('../payments/types.js').WebhookEvent;
    await store.append(evt);
    expect(await store.hasEvent(evt.id)).toBe(true);
  });

  it('findByCustomer filters by customerId', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const e1 = makeEvent({ customerId: 'cust_A' }) as import('../payments/types.js').WebhookEvent;
    const e2 = makeEvent({ customerId: 'cust_B' }) as import('../payments/types.js').WebhookEvent;
    await store.append(e1);
    await store.append(e2);
    const result = await store.findByCustomer('cust_A');
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.length).toBe(1);
      expect(result.value[0].customerId).toBe('cust_A');
    }
  });

  it('findByDateRange returns events within range', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const old = makeEvent({ receivedAt: '2020-01-01T00:00:00Z' }) as import('../payments/types.js').WebhookEvent;
    const recent = makeEvent({ receivedAt: new Date().toISOString() }) as import('../payments/types.js').WebhookEvent;
    await store.append(old);
    await store.append(recent);
    const result = await store.findByDateRange('2025-01-01T00:00:00Z', new Date().toISOString());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.some(e => e.id === recent.id)).toBe(true);
      expect(result.value.some(e => e.id === old.id)).toBe(false);
    }
  });

  it('findByType filters by event type', async () => {
    const { ReceiptStore } = await import('../payments/receipt-store.js');
    const store = new ReceiptStore(storePath);
    const checkout = makeEvent({ type: 'checkout.completed' }) as import('../payments/types.js').WebhookEvent;
    const sub = makeEvent({ type: 'subscription.created' }) as import('../payments/types.js').WebhookEvent;
    await store.append(checkout);
    await store.append(sub);
    const result = await store.findByType('checkout.completed');
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.every(e => e.type === 'checkout.completed')).toBe(true);
    }
  });
});

// ─── MeteringStore — edge cases ───────────────────────────────────────────────

describe('MeteringStore — edge cases', () => {
  let dir: string;

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'metering-'));
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  function makeEvent(timestamp: string, cat = 'llm_call') {
    return { id: randomUUID(), category: cat as import('../metering/types.js').UsageCategory,
      timestamp, provider: 'anthropic', model: 'claude-3', inputTokens: 10,
      outputTokens: 5, estimatedCost: 0.001 };
  }

  it('appendBatch with empty array returns ok immediately', async () => {
    const { MeteringStore } = await import('../metering/store.js');
    const store = new MeteringStore(dir);
    const result = await store.appendBatch([]);
    expect(result.ok).toBe(true);
  });

  it('appendBatch groups events by month into separate files', async () => {
    const { MeteringStore } = await import('../metering/store.js');
    const store = new MeteringStore(dir);
    const events = [
      makeEvent('2026-01-15T10:00:00Z'),
      makeEvent('2026-02-20T10:00:00Z'),
      makeEvent('2026-01-28T10:00:00Z'),
    ] as import('../metering/types.js').UsageEvent[];
    const result = await store.appendBatch(events);
    expect(result.ok).toBe(true);

    const jan = await store.readPeriod({ year: 2026, month: 1, label: '2026-01' });
    expect(jan.ok).toBe(true);
    if (jan.ok) expect(jan.value.length).toBe(2);

    const feb = await store.readPeriod({ year: 2026, month: 2, label: '2026-02' });
    expect(feb.ok).toBe(true);
    if (feb.ok) expect(feb.value.length).toBe(1);
  });

  it('queryRange across month boundary returns all matching events', async () => {
    const { MeteringStore } = await import('../metering/store.js');
    const store = new MeteringStore(dir);
    const events = [
      makeEvent('2026-01-31T23:00:00Z'),
      makeEvent('2026-02-01T01:00:00Z'),
    ] as import('../metering/types.js').UsageEvent[];
    await store.appendBatch(events);
    const result = await store.queryRange('2026-01-31T00:00:00Z', '2026-02-01T23:59:59Z');
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value.length).toBe(2);
  });

  it('readToday returns empty array when no events today', async () => {
    const { MeteringStore } = await import('../metering/store.js');
    const store = new MeteringStore(join(dir, 'empty'));
    const result = await store.readToday();
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value.length).toBe(0);
  });

  it('periodFromDate handles year boundary correctly (Dec→Jan)', async () => {
    const { periodFromDate } = await import('../metering/store.js');
    const p = periodFromDate('2025-12-31T23:59:59Z');
    expect(p.year).toBe(2025);
    expect(p.month).toBe(12);
    expect(p.label).toBe('2025-12');
  });
});

// ─── UsageAnalyzer — uncovered paths ─────────────────────────────────────────

describe('UsageAnalyzer — edge cases', () => {
  it('summarize with no events infers current period', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const summary = analyzer.summarize([]);
    expect(summary.readings.length).toBe(0);
    expect(summary.totals.llmCalls).toBe(0);
    expect(summary.byCategory.llm_call).toBe(0);
  });

  it('detectOverages returns empty array for unlimited (-1) quotas', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const reading = { date: 'today', llmCalls: 9999, toolRuns: 9999, sopRuns: 9999,
      totalInputTokens: 0, totalOutputTokens: 0, totalCostUsd: 0 };
    const quota = { tier: 'enterprise' as const, llmCallsPerDay: -1, toolRunsPerDay: -1,
      sopRunsPerDay: -1, storageBytes: -1 };
    const overages = analyzer.detectOverages(reading, quota);
    expect(overages.length).toBe(0);
  });

  it('detectOverages flags all exceeded categories', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const reading = { date: 'today', llmCalls: 15, toolRuns: 60, sopRuns: 10,
      totalInputTokens: 0, totalOutputTokens: 0, totalCostUsd: 0 };
    const quota = { tier: 'free' as const, llmCallsPerDay: 10, toolRunsPerDay: 50,
      sopRunsPerDay: 5, storageBytes: 100 * 1024 * 1024 };
    const overages = analyzer.detectOverages(reading, quota);
    expect(overages.length).toBe(3);
    const cats = overages.map(o => o.category);
    expect(cats).toContain('llm_call');
    expect(cats).toContain('tool_run');
    expect(cats).toContain('sop_run');
  });

  it('estimateCost sums estimatedCost across all events', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const events = [
      { id: '1', category: 'llm_call' as const, timestamp: new Date().toISOString(),
        provider: 'anthropic', model: 'claude', estimatedCost: 0.01 },
      { id: '2', category: 'llm_call' as const, timestamp: new Date().toISOString(),
        provider: 'anthropic', model: 'claude', estimatedCost: 0.02 },
      { id: '3', category: 'tool_run' as const, timestamp: new Date().toISOString() },
    ] as import('../metering/types.js').UsageEvent[];
    expect(analyzer.estimateCost(events)).toBeCloseTo(0.03, 6);
  });

  it('todayReading returns zero reading when no events today', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const reading = analyzer.todayReading([]);
    expect(reading.llmCalls).toBe(0);
    expect(reading.toolRuns).toBe(0);
    expect(reading.sopRuns).toBe(0);
  });

  it('totalize returns zeroed reading for empty input', async () => {
    const { UsageAnalyzer } = await import('../metering/analyzer.js');
    const analyzer = new UsageAnalyzer();
    const totals = analyzer.totalize([]);
    expect(totals.llmCalls).toBe(0);
    expect(totals.date).toBe('total');
  });
});

// ─── billing command helpers ──────────────────────────────────────────────────

describe('billing command — buildTestPayload via import', () => {
  it('registerBillingCommand exports a function', async () => {
    const mod = await import('../cli/commands/billing.js');
    expect(typeof mod.registerBillingCommand).toBe('function');
  });

  it('registerBillingCommand attaches to commander without throwing', async () => {
    const { Command } = await import('commander');
    const { registerBillingCommand } = await import('../cli/commands/billing.js');
    const program = new Command();
    expect(() => registerBillingCommand(program)).not.toThrow();
    const names = program.commands.map(c => c.name());
    expect(names).toContain('billing');
  });
});

// ─── usage command register ───────────────────────────────────────────────────

describe('usage command registration', () => {
  it('registerUsageCommand attaches to commander without throwing', async () => {
    const { Command } = await import('commander');
    const { registerUsageCommand } = await import('../cli/commands/usage.js');
    const program = new Command();
    expect(() => registerUsageCommand(program)).not.toThrow();
    const names = program.commands.map(c => c.name());
    expect(names).toContain('usage');
  });
});

// ─── analytics command register ──────────────────────────────────────────────

describe('analytics command registration', () => {
  it('registerAnalyticsCommand attaches to commander without throwing', async () => {
    const { Command } = await import('commander');
    const { registerAnalyticsCommand } = await import('../cli/commands/analytics.js');
    const program = new Command();
    expect(() => registerAnalyticsCommand(program)).not.toThrow();
    const names = program.commands.map(c => c.name());
    expect(names).toContain('analytics');
  });
});

// ─── license-admin command register ──────────────────────────────────────────

describe('license-admin command registration', () => {
  it('registerLicenseAdminCommand attaches to commander without throwing', async () => {
    const { Command } = await import('commander');
    const { registerLicenseAdminCommand } = await import('../cli/commands/license-admin.js');
    const program = new Command();
    expect(() => registerLicenseAdminCommand(program)).not.toThrow();
    const names = program.commands.map(c => c.name());
    expect(names).toContain('license-admin');
  });
});
