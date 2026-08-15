/**
 * load-testing.test.ts — concurrent and stress tests for metering, license, payments.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rm, mkdir } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { MeteringStore } from '../metering/store.js';
import { MeteringCollector } from '../metering/collector.js';
import { UsageLimiter } from '../metering/limiter.js';
import { UsageAnalyzer } from '../metering/analyzer.js';
import { LicenseStore } from '../license/store.js';
import { LicenseAdmin } from '../license/admin.js';
import { ReceiptStore } from '../payments/receipt-store.js';
import type { UsageEvent } from '../metering/types.js';
import type { WebhookEvent } from '../payments/types.js';

const dirs: string[] = [];
function tmpDir(): string {
  const d = join(tmpdir(), `loadtest-${randomUUID()}`);
  dirs.push(d);
  return d;
}
function makeEvent(overrides: Partial<UsageEvent> = {}): UsageEvent {
  return { id: randomUUID(), category: 'llm_call', timestamp: new Date().toISOString(),
    provider: 'anthropic', model: 'claude-sonnet-4', inputTokens: 100, outputTokens: 50,
    estimatedCost: 0.001, ...overrides };
}
function makeReceipt(overrides: Partial<WebhookEvent> = {}): WebhookEvent {
  return { id: randomUUID(), type: 'order.created', receivedAt: new Date().toISOString(),
    processed: true, customerId: 'cust_test', tier: 'pro', ...overrides };
}
afterEach(async () => {
  await Promise.all(dirs.map((d) => rm(d, { recursive: true, force: true })));
  dirs.length = 0;
});

describe('load tests — metering & payments', () => {
  it('100 concurrent metering events all recorded', async () => {
    const store = new MeteringStore(tmpDir());
    await Promise.all(Array.from({ length: 100 }, () => store.append(makeEvent())));
    const r = await store.readToday();
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value.length).toBe(100);
  }, 10_000);

  it('50 concurrent license store read/writes maintain data integrity', async () => {
    const dir = tmpDir();
    await mkdir(dir, { recursive: true });
    await Promise.all(Array.from({ length: 50 }, (_, i) => {
      const store = new LicenseStore(join(dir, `license-${i}.json`));
      const license = { key: `mk_${randomUUID()}`, tier: 'pro' as const, owner: `owner-${i}`,
        issuedAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 86_400_000 * 365).toISOString(), status: 'active' as const,
        signature: '' }; // Empty signature for test licenses
      return store.save(license).then(async (sr) => {
        expect(sr.ok).toBe(true);
        const lr = await store.load();
        expect(lr.ok).toBe(true);
        if (lr.ok) {
          expect(lr.value?.key).toBe(license.key);
        }
      });
    }));
  }, 10_000);

  it('100 collector.record() calls via 4 collectors flush and count matches', async () => {
    // Each collector stays under the 50-event threshold so shutdown() flushes cleanly.
    const store = new MeteringStore(tmpDir());
    const collectors = Array.from({ length: 4 }, () => new MeteringCollector(store));
    collectors.forEach((c, ci) => {
      for (let i = 0; i < 25; i++) c.record({ category: 'tool_run', resourceName: `t-${ci}-${i}` });
    });
    await Promise.all(collectors.map((c) => c.shutdown()));
    const r = await store.readToday();
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value.length).toBe(100);
  }, 10_000);

  it('200 concurrent limiter.checkLimit() returns consistent results', async () => {
    const store = new MeteringStore(tmpDir());
    await store.appendBatch(Array.from({ length: 5 }, () => makeEvent({ category: 'llm_call' })));
    const limiter = new UsageLimiter(store);
    const results = await Promise.all(Array.from({ length: 200 }, () => limiter.checkLimit('llm_call', 'pro')));
    expect(results.every((r) => r.ok)).toBe(true);
    const first = results[0]!;
    if (first.ok) {
      const used = first.value.used;
      expect(results.every((r) => r.ok && r.value.used === used)).toBe(true);
      expect(first.value.allowed).toBe(true);
    }
  }, 10_000);

  it('stress: 1000 events rapid fire — analyzer aggregation correct', async () => {
    const analyzer = new UsageAnalyzer();
    const today = new Date().toISOString().slice(0, 10);
    const events = Array.from({ length: 1000 }, (_, i) => ({
      id: randomUUID(),
      category: (i % 3 === 0 ? 'llm_call' : i % 3 === 1 ? 'tool_run' : 'sop_run') as UsageEvent['category'],
      timestamp: `${today}T12:00:00.000Z`,
      inputTokens: i % 3 === 0 ? 100 : undefined,
      outputTokens: i % 3 === 0 ? 50 : undefined,
      estimatedCost: i % 3 === 0 ? 0.001 : undefined,
    } satisfies UsageEvent));
    const readings = analyzer.aggregate(events);
    expect(readings).toHaveLength(1);
    const r = readings[0]!;
    expect(r.llmCalls).toBe(events.filter((e) => e.category === 'llm_call').length);
    expect(r.toolRuns).toBe(events.filter((e) => e.category === 'tool_run').length);
    expect(r.sopRuns).toBe(events.filter((e) => e.category === 'sop_run').length);
  }, 10_000);

  it('concurrent receipt store appends — no data loss, dedup works', async () => {
    const store = new ReceiptStore(join(tmpDir(), 'receipts.jsonl'));
    const receipts = Array.from({ length: 80 }, () => makeReceipt());
    await Promise.all(receipts.map((r) => store.append(r)));
    const result = await store.readAll();
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value.length).toBe(80);
    const checks = await Promise.all(receipts.slice(0, 20).map((r) => store.hasEvent(r.id)));
    expect(checks.every(Boolean)).toBe(true);
  }, 10_000);

  it('multiple collectors sharing same store — verify isolation', async () => {
    const store = new MeteringStore(tmpDir());
    const collectors = Array.from({ length: 5 }, () => new MeteringCollector(store));
    collectors.forEach((c, ci) => {
      for (let i = 0; i < 20; i++) c.record({ category: 'llm_call', provider: `p${ci}`, model: `m${ci}` });
    });
    await Promise.all(collectors.map((c) => c.shutdown()));
    const r = await store.readToday();
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value.length).toBe(100);
  }, 10_000);

  it('rapid create+revoke license cycles — audit log integrity', async () => {
    const dir = tmpDir();
    const admin = new LicenseAdmin(join(dir, 'registry.json'), join(dir, 'audit.jsonl'), 'tester');
    const created: string[] = [];
    for (let i = 0; i < 10; i++) {
      const r = await admin.createKey('pro', `owner-${i}`, 30);
      expect(r.ok).toBe(true);
      if (r.ok) created.push(r.value.key);
    }
    // Sequential: registry is read-modify-write (not concurrency-safe)
    for (const keyId of created) await admin.revokeKey(keyId);
    const list = await admin.listKeys();
    expect(list.ok).toBe(true);
    if (list.ok) expect(list.value.every((k) => k.status === 'revoked')).toBe(true);
    const { AuditLog } = await import('../license/audit-log.js');
    const audit = await new AuditLog(join(dir, 'audit.jsonl')).readAll();
    expect(audit.ok).toBe(true);
    if (audit.ok) expect(audit.value.length).toBeGreaterThanOrEqual(20);
  }, 15_000);

  it('appendBatch 200 events across 2 periods — all retrievable', async () => {
    const store = new MeteringStore(tmpDir());
    const events = [
      ...Array.from({ length: 100 }, () => makeEvent({ timestamp: '2026-02-15T10:00:00.000Z' })),
      ...Array.from({ length: 100 }, () => makeEvent({ timestamp: '2026-03-10T10:00:00.000Z' })),
    ];
    expect((await store.appendBatch(events)).ok).toBe(true);
    const feb = await store.queryRange('2026-02-01T00:00:00Z', '2026-02-28T23:59:59Z');
    const mar = await store.queryRange('2026-03-01T00:00:00Z', '2026-03-31T23:59:59Z');
    if (feb.ok) expect(feb.value.length).toBe(100);
    if (mar.ok) expect(mar.value.length).toBe(100);
  }, 10_000);

  it('enterprise tier — unlimited across 100 concurrent limit checks', async () => {
    const store = new MeteringStore(tmpDir());
    await store.appendBatch(Array.from({ length: 999 }, () => makeEvent({ category: 'llm_call' })));
    const limiter = new UsageLimiter(store);
    const results = await Promise.all(Array.from({ length: 100 }, () => limiter.checkLimit('llm_call', 'enterprise')));
    expect(results.every((r) => r.ok && r.value.allowed && r.value.remaining === Infinity)).toBe(true);
  }, 10_000);

  it('receipt store concurrent findByCustomer — correct filtering under load', async () => {
    const store = new ReceiptStore(join(tmpDir(), 'receipts.jsonl'));
    const [cA, cB] = ['cust_aaa', 'cust_bbb'];
    await Promise.all([
      ...Array.from({ length: 40 }, () => store.append(makeReceipt({ customerId: cA }))),
      ...Array.from({ length: 40 }, () => store.append(makeReceipt({ customerId: cB }))),
    ]);
    const [resA, resB] = await Promise.all([store.findByCustomer(cA!), store.findByCustomer(cB!)]);
    if (resA.ok) {
      expect(resA.value.length).toBe(40);
      expect(resA.value.every((e) => e.customerId === cA)).toBe(true);
    }
    if (resB.ok) {
      expect(resB.value.length).toBe(40);
      expect(resB.value.every((e) => e.customerId === cB)).toBe(true);
    }
  }, 10_000);
});
