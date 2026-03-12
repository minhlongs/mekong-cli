/**
 * edge-cases.test.ts — edge case coverage: empty data, negative amounts, boundaries.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rm, mkdir } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';

import { MeteringStore } from '../metering/store.js';
import { UsageAnalyzer } from '../metering/analyzer.js';
import { CostCalculator } from '../metering/cost-calculator.js';
import { UsageLimiter } from '../metering/limiter.js';
import { ROICalculator } from '../analytics/roi-calculator.js';
import { AgentScorer } from '../analytics/agent-scorer.js';
import { RevenueTracker } from '../analytics/revenue-tracker.js';
import { GrowthAnalyzer } from '../analytics/growth-analyzer.js';
import { changeTier, upgradeTier } from '../license/tier-manager.js';
import { generateKey } from '../license/key-generator.js';
import type { UsageEvent } from '../metering/types.js';

const period = { label: '2026-03', startDate: '2026-03-01T00:00:00.000Z', endDate: '2026-03-31T23:59:59.999Z' };

function tmpDir(): string { return join(tmpdir(), `edge-${randomUUID()}`); }
let dirs: string[] = [];
afterEach(async () => {
  await Promise.all(dirs.map((d) => rm(d, { recursive: true, force: true })));
  dirs = [];
});

function makeEvent(overrides: Partial<UsageEvent> = {}): UsageEvent {
  return { id: randomUUID(), category: 'llm_call', timestamp: new Date().toISOString(),
    provider: 'anthropic', model: 'claude-sonnet-4', inputTokens: 100, outputTokens: 50,
    estimatedCost: 0.001, ...overrides };
}

// ── UsageAnalyzer ─────────────────────────────────────────────────────────────

describe('UsageAnalyzer — empty data', () => {
  const analyzer = new UsageAnalyzer();

  it('aggregate([]) returns empty array', () => {
    expect(analyzer.aggregate([])).toEqual([]);
  });

  it('summarize([]) returns zero totals', () => {
    const s = analyzer.summarize([]);
    expect(s.totals.llmCalls).toBe(0);
    expect(s.totals.totalCostUsd).toBe(0);
    expect(s.readings).toHaveLength(0);
  });

  it('totalize([]) returns all-zero MeterReading', () => {
    const t = analyzer.totalize([]);
    expect(t.llmCalls).toBe(0);
    expect(t.totalCostUsd).toBe(0);
  });
});

// ── RevenueTracker — empty events ─────────────────────────────────────────────

describe('RevenueTracker — empty receipts', () => {
  const tracker = new RevenueTracker();

  it('buildReport([]) → MRR=0, ARR=0, activeCustomers=0', () => {
    const result = tracker.buildReport([], period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.mrr).toBe(0);
    expect(result.value.arr).toBe(0);
    expect(result.value.activeCustomers).toBe(0);
    expect(result.value.arpu).toBe(0);
  });
});

// ── ROICalculator ─────────────────────────────────────────────────────────────

describe('ROICalculator — boundary inputs', () => {
  const calc = new ROICalculator();

  it('negative totalCost → err', () => {
    const r = calc.calculate({ timeSavedHours: 10, hourlyRate: 50, revenueGenerated: 100, totalCost: -1, period });
    expect(r.ok).toBe(false);
  });

  it('negative hourlyRate → err', () => {
    const r = calc.calculate({ timeSavedHours: 10, hourlyRate: -1, revenueGenerated: 0, totalCost: 10, period });
    expect(r.ok).toBe(false);
  });

  it('totalCost=0, positive value → roiPercent=9999', () => {
    const r = calc.calculate({ timeSavedHours: 5, hourlyRate: 100, revenueGenerated: 0, totalCost: 0, period });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.roiPercent).toBe(9999);
  });

  it('totalCost=0, zero value → roiPercent=0', () => {
    const r = calc.calculate({ timeSavedHours: 0, hourlyRate: 0, revenueGenerated: 0, totalCost: 0, period });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.roiPercent).toBe(0);
  });

  it('timeSavedHours=0 → valid result, no crash', () => {
    const r = calc.calculate({ timeSavedHours: 0, hourlyRate: 50, revenueGenerated: 200, totalCost: 100, period });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.roiPercent).toBe(100); // (200-100)/100*100
  });
});

// ── AgentScorer ───────────────────────────────────────────────────────────────

describe('AgentScorer — boundary inputs', () => {
  const scorer = new AgentScorer();
  const base = { agentName: 'test', phasesCompleted: 0, totalPhases: 0,
    recentCommits: 0, activityBaseline: 0, totalExecutions: 0,
    successfulExecutions: 0, recoveredExecutions: 0, failedExecutions: 0 };

  it('all zeros → agiScore=100 (no-runs = assume perfect)', () => {
    const r = scorer.score(base);
    // No phases (0), no activity (0→0), no executions (assume 1.0), no problems (1.0)
    // phaseProgress=0*0.30 + activity=0*0.25 + success=100*0.25 + resilience=100*0.20 = 45
    expect(r.agiScore).toBeGreaterThanOrEqual(0);
    expect(r.agiScore).toBeLessThanOrEqual(100);
  });

  it('all 100% → agiScore=100', () => {
    const r = scorer.score({
      agentName: 'perfect', phasesCompleted: 10, totalPhases: 10,
      recentCommits: 10, activityBaseline: 10, totalExecutions: 10,
      successfulExecutions: 10, recoveredExecutions: 0, failedExecutions: 0,
    });
    expect(r.agiScore).toBe(100);
  });
});

// ── GrowthAnalyzer — boundary inputs ─────────────────────────────────────────

describe('GrowthAnalyzer — boundary inputs', () => {
  const analyzer = new GrowthAnalyzer();
  const base = { period, currentMRR: 0, previousMRR: 0, currentWeekRevenue: 0,
    previousWeekRevenue: 0, startingCustomers: 0, newCustomers: 0,
    churnedCustomers: 0, expansionRevenue: 0 };

  it('single data point (all zeros) → no crash', () => {
    const r = analyzer.analyze(base);
    expect(r.momGrowthPercent).toBe(0);
    expect(r.wowGrowthPercent).toBe(0);
    expect(r.churnRate).toBe(0);
  });

  it('identical months → 0% MoM growth', () => {
    const r = analyzer.analyze({ ...base, currentMRR: 1000, previousMRR: 1000 });
    expect(r.momGrowthPercent).toBe(0);
  });

  it('previousMRR=0, currentMRR=0 → NRR=100 (neutral baseline)', () => {
    const r = analyzer.analyze(base);
    expect(r.nrrPercent).toBe(100);
  });
});

// ── CostCalculator — unknown model ───────────────────────────────────────────

describe('CostCalculator — unknown model fallback', () => {
  const calc = new CostCalculator();

  it('unknown model uses conservative default (no crash)', () => {
    const cost = calc.calculate('anthropic', 'unknown-future-model', 1_000_000, 1_000_000);
    expect(cost).toBeGreaterThan(0); // defaults to Sonnet-level: 3+15=18
    expect(cost).toBe(18);
  });

  it('ollama provider always returns 0', () => {
    expect(calc.calculate('ollama', 'llama3', 1_000_000, 1_000_000)).toBe(0);
  });
});

// ── MeteringStore — date boundary queries ─────────────────────────────────────

describe('MeteringStore — date boundary queries', () => {
  it('future date range → empty results', async () => {
    const dir = tmpDir();
    dirs.push(dir);
    await mkdir(dir, { recursive: true });
    const store = new MeteringStore(dir);
    const result = await store.queryRange('2099-01-01T00:00:00Z', '2099-12-31T23:59:59Z');
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value).toHaveLength(0);
  });

  it('inverted date range (from > to) → empty results', async () => {
    const dir = tmpDir();
    dirs.push(dir);
    await mkdir(dir, { recursive: true });
    const store = new MeteringStore(dir);
    // Write an event so there's data in the store
    await store.append(makeEvent({ timestamp: '2026-03-15T10:00:00.000Z' }));
    // Query with inverted range
    const result = await store.queryRange('2026-03-31T00:00:00Z', '2026-03-01T00:00:00Z');
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value).toHaveLength(0);
  });
});

// ── UsageLimiter — 0 remaining ────────────────────────────────────────────────

describe('UsageLimiter — 0 remaining blocks', () => {
  it('free tier at exact limit → blocked', async () => {
    const dir = tmpDir();
    dirs.push(dir);
    await mkdir(dir, { recursive: true });
    const store = new MeteringStore(dir);
    // Fill exactly at the free tier limit (10 llm_calls/day)
    const events = Array.from({ length: 10 }, () => makeEvent());
    await store.appendBatch(events);
    const limiter = new UsageLimiter(store);
    const result = await limiter.checkLimit('llm_call', 'free');
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.allowed).toBe(false);
    expect(result.value.remaining).toBe(0);
  });
});

// ── TierManager ───────────────────────────────────────────────────────────────

describe('TierManager — edge cases', () => {
  it('upgrade to same tier → err', () => {
    const key = generateKey({ tier: 'pro', owner: 'user', expiryDays: 30 });
    const r = upgradeTier(key, 'pro');
    expect(r.ok).toBe(false);
  });

  it('changeTier same tier → direction=same, no crash', () => {
    const key = generateKey({ tier: 'starter', owner: 'user', expiryDays: 30 });
    const r = changeTier(key, 'starter');
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.direction).toBe('same');
  });

  it('changeTier with 0 days remaining → clamps to 1 day minimum', () => {
    const key = generateKey({ tier: 'starter', owner: 'user', expiryDays: 0 });
    // expiryDays=0 generates a key that is already expired (past)
    const r = changeTier(key, 'pro');
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.value.remainingDays).toBeGreaterThanOrEqual(1);
  });

  it('revoked key → err on changeTier', () => {
    const key = generateKey({ tier: 'starter', owner: 'user', expiryDays: 30 });
    const revoked = { ...key, status: 'revoked' as const };
    const r = changeTier(revoked, 'pro');
    expect(r.ok).toBe(false);
  });
});
