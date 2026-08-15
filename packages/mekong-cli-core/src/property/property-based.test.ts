/**
 * property-based.test.ts — Random-input property tests for ROIaaS functions.
 * No external libraries. Uses Math.random() inline generators.
 */
import { describe, it, expect } from 'vitest';
import { computeSignature, verifyLicense } from '../license/verifier.js';
import { generateKey } from '../license/key-generator.js';
import { tierMeetsMinimum } from '../license/feature-map.js';
import { TIER_ORDER } from '../license/types.js';
import type { LicenseKey, LicenseTier } from '../license/types.js';
import { ROICalculator } from '../analytics/roi-calculator.js';
import { AgentScorer } from '../analytics/agent-scorer.js';
import { CostCalculator } from '../metering/cost-calculator.js';
import { GrowthAnalyzer } from '../analytics/growth-analyzer.js';
import { RevenueTracker } from '../analytics/revenue-tracker.js';

// ─── Generators ───────────────────────────────────────────────────────────────

const TIERS: LicenseTier[] = ['free', 'starter', 'pro', 'enterprise'];
const randInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;
const randFloat = (min: number, max: number) => Math.random() * (max - min) + min;
const randTier = (): LicenseTier => TIERS[randInt(0, TIERS.length - 1)];
const futureISO = (days: number) => new Date(Date.now() + days * 86_400_000).toISOString();

function makeLic(tier: LicenseTier = 'starter', owner = 'user'): LicenseKey {
  const partial = {
    key: `RAAS-${tier.toUpperCase()}-prop${randInt(0, 999999).toString(16)}`,
    tier, status: 'active' as const,
    issuedAt: new Date().toISOString(), expiresAt: futureISO(30), owner,
  };
  return { ...partial, signature: computeSignature(partial) };
}

const period = {
  label: '2025-01',
  startDate: '2025-01-01T00:00:00.000Z',
  endDate: '2025-01-31T23:59:59.999Z',
};

// ─── computeSignature determinism ─────────────────────────────────────────────

describe('computeSignature determinism', () => {
  it('same inputs always produce same signature (50 runs)', () => {
    for (let i = 0; i < 50; i++) {
      const lic = makeLic(randTier(), `owner-${i}`);
      const partial = { key: lic.key, tier: lic.tier, status: lic.status, issuedAt: lic.issuedAt, expiresAt: lic.expiresAt, owner: lic.owner };
      expect(computeSignature(partial)).toBe(computeSignature(partial));
    }
  });
});

// ─── verifyLicense idempotency ────────────────────────────────────────────────

describe('verifyLicense idempotency', () => {
  it('sign then verify is always valid for active non-expired keys (100 runs)', () => {
    for (let i = 0; i < 100; i++) {
      expect(verifyLicense(makeLic(randTier(), `owner-${i}`)).valid).toBe(true);
    }
  });
});

// ─── generateKey uniqueness ───────────────────────────────────────────────────

describe('generateKey uniqueness', () => {
  it('100 generated keys are all unique', () => {
    const keys = new Set<string>();
    for (let i = 0; i < 100; i++) keys.add(generateKey({ tier: randTier(), owner: `o-${i}` }).key);
    expect(keys.size).toBe(100);
  });
});

// ─── generateKey format ───────────────────────────────────────────────────────

describe('generateKey format', () => {
  it('all keys match RAAS-{TIER}-{hex16} pattern (100 runs)', () => {
    const pat = /^RAAS-[A-Z]+-[0-9a-f]{16}$/;
    for (let i = 0; i < 100; i++) expect(generateKey({ tier: randTier(), owner: `o-${i}` }).key).toMatch(pat);
  });
});

// ─── ROICalculator non-negative ───────────────────────────────────────────────

describe('ROICalculator non-negative', () => {
  const calc = new ROICalculator();
  it('random positive inputs produce finite roiPercent (50 runs)', () => {
    for (let i = 0; i < 50; i++) {
      const r = calc.calculate({ timeSavedHours: randFloat(0, 500), hourlyRate: randFloat(0, 500), revenueGenerated: randFloat(0, 100000), totalCost: randFloat(0.01, 5000), period });
      expect(r.ok).toBe(true);
      if (r.ok) {
        expect(Number.isFinite(r.value.roiPercent)).toBe(true);
        expect(Number.isNaN(r.value.roiPercent)).toBe(false);
      }
    }
  });
});

// ─── ROICalculator monotonicity ───────────────────────────────────────────────

describe('ROICalculator monotonicity', () => {
  const calc = new ROICalculator();
  it('higher revenue yields higher or equal ROI (50 pairs)', () => {
    for (let i = 0; i < 50; i++) {
      const base = randFloat(0, 5000);
      const shared = { timeSavedHours: randFloat(0, 100), hourlyRate: randFloat(10, 200), totalCost: randFloat(1, 1000), period };
      const r1 = calc.calculate({ ...shared, revenueGenerated: base });
      const r2 = calc.calculate({ ...shared, revenueGenerated: base + randFloat(1, 5000) });
      if (r1.ok && r2.ok) expect(r2.value.roiPercent).toBeGreaterThanOrEqual(r1.value.roiPercent);
    }
  });
});

// ─── AgentScorer range ────────────────────────────────────────────────────────

describe('AgentScorer range', () => {
  const scorer = new AgentScorer();
  it('random inputs produce agiScore always in 0-100 (50 runs)', () => {
    for (let i = 0; i < 50; i++) {
      const total = randInt(1, 100);
      const successful = randInt(0, total);
      const failed = total - successful;
      const recovered = randInt(0, failed);
      const s = scorer.score({ agentName: `a-${i}`, phasesCompleted: randInt(0, 20), totalPhases: randInt(1, 20), recentCommits: randInt(0, 50), activityBaseline: randInt(1, 50), totalExecutions: total, successfulExecutions: successful, recoveredExecutions: recovered, failedExecutions: failed - recovered });
      expect(s.agiScore).toBeGreaterThanOrEqual(0);
      expect(s.agiScore).toBeLessThanOrEqual(100);
    }
  });
});

// ─── AgentScorer determinism ──────────────────────────────────────────────────

describe('AgentScorer determinism', () => {
  const scorer = new AgentScorer();
  it('same inputs produce same score (30 runs)', () => {
    for (let i = 0; i < 30; i++) {
      const inp = { agentName: `a-${i}`, phasesCompleted: randInt(0, 10), totalPhases: randInt(1, 10), recentCommits: randInt(0, 20), activityBaseline: randInt(1, 20), totalExecutions: randInt(1, 50), successfulExecutions: randInt(0, 30), recoveredExecutions: randInt(0, 10), failedExecutions: randInt(0, 10) };
      expect(scorer.score(inp).agiScore).toBe(scorer.score(inp).agiScore);
    }
  });
});

// ─── CostCalculator non-negative ─────────────────────────────────────────────

describe('CostCalculator non-negative', () => {
  const calc = new CostCalculator();
  const models = calc.knownModels();
  it('any known model+tokens combination yields cost >= 0 (50 runs)', () => {
    for (let i = 0; i < 50; i++) {
      const key = models[randInt(0, models.length - 1)];
      const parts = key.split('/');
      const [prov, model] = parts.length > 1 ? [parts[0], parts.slice(1).join('/')] : ['anthropic', key];
      expect(calc.calculate(prov, model, randInt(0, 100000), randInt(0, 50000))).toBeGreaterThanOrEqual(0);
    }
  });
});

// ─── tierMeetsMinimum reflexivity ─────────────────────────────────────────────

describe('tierMeetsMinimum reflexivity', () => {
  it('every tier meets its own minimum', () => {
    for (const tier of TIER_ORDER) expect(tierMeetsMinimum(tier, tier)).toBe(true);
  });
});

// ─── tierMeetsMinimum transitivity ────────────────────────────────────────────

describe('tierMeetsMinimum transitivity', () => {
  it('if A >= B and B >= C then A >= C (all tier triples)', () => {
    for (const a of TIER_ORDER)
      for (const b of TIER_ORDER)
        for (const c of TIER_ORDER)
          if (tierMeetsMinimum(a, b) && tierMeetsMinimum(b, c))
            expect(tierMeetsMinimum(a, c)).toBe(true);
  });
});

// ─── GrowthAnalyzer single data point ────────────────────────────────────────

describe('GrowthAnalyzer single data point', () => {
  const analyzer = new GrowthAnalyzer();
  it('single non-zero data point never crashes (30 runs)', () => {
    for (let i = 0; i < 30; i++) {
      expect(() => analyzer.analyze({
        period, currentMRR: randFloat(0, 10000), previousMRR: 0,
        currentWeekRevenue: randFloat(0, 5000), previousWeekRevenue: 0,
        startingCustomers: 0, newCustomers: randInt(0, 20),
        churnedCustomers: 0, expansionRevenue: randFloat(0, 1000),
      })).not.toThrow();
    }
  });
});

// ─── GrowthAnalyzer result fields finite ─────────────────────────────────────

describe('GrowthAnalyzer result fields finite', () => {
  const analyzer = new GrowthAnalyzer();
  it('all numeric output fields are finite (30 runs)', () => {
    for (let i = 0; i < 30; i++) {
      const g = analyzer.analyze({
        period, currentMRR: randFloat(0, 50000), previousMRR: randFloat(0, 50000),
        currentWeekRevenue: randFloat(0, 10000), previousWeekRevenue: randFloat(0, 10000),
        startingCustomers: randInt(0, 200), newCustomers: randInt(0, 50),
        churnedCustomers: randInt(0, 20), expansionRevenue: randFloat(0, 5000),
      });
      expect(Number.isFinite(g.momGrowthPercent)).toBe(true);
      expect(Number.isFinite(g.wowGrowthPercent)).toBe(true);
      expect(Number.isFinite(g.churnRate)).toBe(true);
      expect(Number.isFinite(g.nrrPercent)).toBe(true);
    }
  });
});

// ─── RevenueTracker empty array ───────────────────────────────────────────────

describe('RevenueTracker empty array', () => {
  const tracker = new RevenueTracker();
  it('empty events array yields MRR=0 and ARR=0', () => {
    const r = tracker.buildReport([], period);
    expect(r.ok).toBe(true);
    if (r.ok) { expect(r.value.mrr).toBe(0); expect(r.value.arr).toBe(0); }
  });
});

// ─── RevenueTracker ARR = MRR * 12 ───────────────────────────────────────────

describe('RevenueTracker ARR invariant', () => {
  const tracker = new RevenueTracker();
  it('ARR always equals MRR * 12 (30 runs)', () => {
    for (let i = 0; i < 30; i++) {
      const mrr = randFloat(0, 100000);
      const r = tracker.buildFromMRR({ mrr, activeCustomers: randInt(0, 100), tierDistribution: { free: 0, starter: randInt(0, 10), pro: randInt(0, 5), enterprise: randInt(0, 2) }, period });
      // Both mrr and arr are independently rounded to 2 dp, so allow 0.01 slack per month (0.12 total)
      expect(Math.abs(r.arr - r.mrr * 12)).toBeLessThanOrEqual(0.12);
    }
  });
});

// ─── Additional boundary property tests ─────────────────────────────────────

describe('ROICalculator boundary properties', () => {
  const roi = new ROICalculator();

  it('zero cost yields Infinity or very high ROI', () => {
    const r = roi.calculate({ timeSavedHours: 10, hourlyRate: 100, revenueGenerated: 500, totalCost: 0, period });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value.roiPercent).toBeGreaterThan(0);
  });

  it('equal cost and value yields ~0% ROI net', () => {
    const cost = 1000;
    const r = roi.calculate({ timeSavedHours: 0, hourlyRate: 0, revenueGenerated: cost, totalCost: cost, period });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value.roiPercent).toBeCloseTo(0, 0);
  });

  it('negative revenue returns error result', () => {
    const r = roi.calculate({ timeSavedHours: 0, hourlyRate: 0, revenueGenerated: -100, totalCost: 50, period });
    expect(r.ok).toBe(false);
  });
});

describe('AgentScorer boundary properties', () => {
  const scorer = new AgentScorer();

  it('perfect agent scores near 100', () => {
    const r = scorer.score({ agentName: 'perfect', phasesCompleted: 10, totalPhases: 10, recentCommits: 10, activityBaseline: 10, totalExecutions: 100, successfulExecutions: 100, recoveredExecutions: 0, failedExecutions: 0 });
    expect(r.agiScore).toBeGreaterThanOrEqual(90);
  });

  it('zero-activity agent scores below 50', () => {
    const r = scorer.score({ agentName: 'idle', phasesCompleted: 0, totalPhases: 10, recentCommits: 0, activityBaseline: 10, totalExecutions: 0, successfulExecutions: 0, recoveredExecutions: 0, failedExecutions: 0 });
    expect(r.agiScore).toBeLessThanOrEqual(50);
  });

  it('all-failed agent has low score', () => {
    const r = scorer.score({ agentName: 'fail', phasesCompleted: 0, totalPhases: 10, recentCommits: 5, activityBaseline: 10, totalExecutions: 100, successfulExecutions: 0, recoveredExecutions: 0, failedExecutions: 100 });
    expect(r.agiScore).toBeLessThanOrEqual(40);
  });

  it('high recovery boosts resilience dimension', () => {
    const base = scorer.score({ agentName: 'no-recovery', phasesCompleted: 5, totalPhases: 10, recentCommits: 5, activityBaseline: 10, totalExecutions: 100, successfulExecutions: 50, recoveredExecutions: 0, failedExecutions: 50 });
    const withRecovery = scorer.score({ agentName: 'recovery', phasesCompleted: 5, totalPhases: 10, recentCommits: 5, activityBaseline: 10, totalExecutions: 100, successfulExecutions: 50, recoveredExecutions: 40, failedExecutions: 10 });
    expect(withRecovery.agiScore).toBeGreaterThan(base.agiScore);
  });
});

describe('CostCalculator boundary properties', () => {
  const calc = new CostCalculator();

  it('zero tokens = zero cost', () => {
    const cost = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 0, 0);
    expect(cost).toBe(0);
  });

  it('output tokens always cost more than input tokens for same count', () => {
    const inputOnlyCost = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 1000, 0);
    const outputOnlyCost = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 0, 1000);
    expect(outputOnlyCost).toBeGreaterThanOrEqual(inputOnlyCost);
  });

  it('cost scales linearly with token count', () => {
    const cost1x = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 1000, 500);
    const cost2x = calc.calculate('anthropic', 'claude-sonnet-4-20250514', 2000, 1000);
    expect(Math.abs(cost2x - cost1x * 2)).toBeLessThan(0.001);
  });
});
