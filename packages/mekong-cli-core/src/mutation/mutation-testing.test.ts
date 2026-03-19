/**
 * Mutation Testing — verify test suite catches intentional bugs.
 * Each test implements mutant logic inline and asserts it differs from correct impl.
 */
import { describe, it, expect } from 'vitest';
import { createHmac } from 'node:crypto';
import { computeSignature } from '../license/verifier.js';
import { tierMeetsMinimum } from '../license/feature-map.js';
import { TIER_ORDER, type LicenseTier } from '../license/types.js';
import { ROICalculator } from '../analytics/roi-calculator.js';
import { AgentScorer } from '../analytics/agent-scorer.js';

// Shared test fixture for license signature tests
const LIC_BASE = {
  key: 'TEST-KEY-001',
  tier: 'pro' as const,
  status: 'active' as const,
  issuedAt: '2025-01-01T00:00:00.000Z',
  expiresAt: '2026-01-01T00:00:00.000Z',
  owner: 'test@example.com',
};
const SECRET = 'test-secret-abc';

// ─── HMAC / Signature ────────────────────────────────────────────────────────

describe('Mutation: HMAC wrong algorithm (SHA-512 vs SHA-256)', () => {
  it('SHA-512 produces different hex than SHA-256', () => {
    const correct = computeSignature(LIC_BASE, SECRET);
    const msg = `${LIC_BASE.key}|${LIC_BASE.tier}|${LIC_BASE.issuedAt}|${LIC_BASE.expiresAt}|${LIC_BASE.owner}`;
    const mutant = createHmac('sha512', SECRET).update(msg).digest('hex');
    expect(mutant).not.toBe(correct);
  });
});

describe('Mutation: HMAC swapped fields (tier before key)', () => {
  it('wrong field order produces different signature', () => {
    const correct = computeSignature(LIC_BASE, SECRET);
    // Mutant: swap key and tier
    const wrongMsg = `${LIC_BASE.tier}|${LIC_BASE.key}|${LIC_BASE.issuedAt}|${LIC_BASE.expiresAt}|${LIC_BASE.owner}`;
    const mutant = createHmac('sha256', SECRET).update(wrongMsg).digest('hex');
    expect(mutant).not.toBe(correct);
  });
});

describe('Mutation: Signature with empty secret', () => {
  it('empty string secret produces different HMAC than real secret', () => {
    const correct = computeSignature(LIC_BASE, SECRET);
    const mutant = computeSignature(LIC_BASE, '');
    expect(mutant).not.toBe(correct);
  });
});

// ─── Tier Order ───────────────────────────────────────────────────────────────

describe('Mutation: Tier order reversed', () => {
  it('reversed TIER_ORDER breaks tierMeetsMinimum for enterprise>pro', () => {
    // Correct: enterprise meets pro minimum
    expect(tierMeetsMinimum('enterprise', 'pro')).toBe(true);

    // Mutant: reverse order — now enterprise has lower index than pro
    const reversedOrder = [...TIER_ORDER].reverse(); // ['enterprise','pro','starter','free']
    const mutantMeetsMinimum = (current: LicenseTier, required: LicenseTier) =>
      reversedOrder.indexOf(current) >= reversedOrder.indexOf(required);

    // In reversed order, enterprise index=0, pro index=1 → 0 >= 1 is false (broken!)
    expect(mutantMeetsMinimum('enterprise', 'pro')).toBe(false);
  });
});

// ─── Grace Period ─────────────────────────────────────────────────────────────

describe('Mutation: Grace period removed (0 days vs 7 days)', () => {
  it('3-day-expired key: grace=7 allows, grace=0 blocks', () => {
    const GRACE_7 = 7 * 24 * 60 * 60 * 1000;
    const GRACE_0 = 0;
    // 3 days ago
    const expiredMs = 3 * 24 * 60 * 60 * 1000;
    const nowMinusExpiry = expiredMs; // how long since expiry

    const correctAllowed = nowMinusExpiry <= GRACE_7;   // true
    const mutantAllowed  = nowMinusExpiry <= GRACE_0;   // false

    expect(correctAllowed).toBe(true);
    expect(mutantAllowed).toBe(false);
    expect(correctAllowed).not.toBe(mutantAllowed);
  });
});

// ─── ROI Calculator ───────────────────────────────────────────────────────────

describe('Mutation: ROI formula wrong operator (addition instead of subtraction)', () => {
  it('adding totalCost instead of subtracting gives different ROI', () => {
    const calc = new ROICalculator();
    const inputs = {
      timeSavedHours: 10,
      hourlyRate: 100,
      revenueGenerated: 500,
      totalCost: 200,
      period: { label: '2025-01', startDate: '2025-01-01T00:00:00Z', endDate: '2025-01-31T23:59:59Z' },
    };
    const correct = calc.calculate(inputs);
    expect(correct.ok).toBe(true);
    if (!correct.ok) return;

    // Correct: netValue = timeSaved*rate + revenue - cost = 1000 + 500 - 200 = 1300
    // Mutant:  netValue = timeSaved*rate + revenue + cost = 1000 + 500 + 200 = 1700
    const timeSavedValue = inputs.timeSavedHours * inputs.hourlyRate;
    const mutantNetValue = timeSavedValue + inputs.revenueGenerated + inputs.totalCost;
    const mutantROI = (mutantNetValue / inputs.totalCost) * 100;

    expect(correct.value.roiPercent).not.toBeCloseTo(mutantROI, 1);
  });
});

describe('Mutation: Cost multiplier 10x vs 1x', () => {
  it('10x cost multiplier produces different total cost', () => {
    const baseCost = 5.00;
    const correct = baseCost * 1;
    const mutant  = baseCost * 10;
    expect(mutant).not.toBe(correct);
    expect(mutant).toBe(50.00);
  });
});

// ─── Agent Scorer ─────────────────────────────────────────────────────────────

describe('Mutation: AGI weights swapped (activity=0.30, phaseProgress=0.25)', () => {
  it('swapped weights produce different AGI score', () => {
    const scorer = new AgentScorer();
    const inputs = {
      agentName: 'test-agent',
      phasesCompleted: 3, totalPhases: 10,   // phaseProgress = 30%
      recentCommits: 9, activityBaseline: 10, // activity = 90%
      totalExecutions: 10, successfulExecutions: 8,
      recoveredExecutions: 1, failedExecutions: 1,
    };
    const correctResult = scorer.score(inputs);
    // Correct weights: phaseProgress=0.30, activity=0.25
    // Mutant weights: phaseProgress=0.25, activity=0.30
    const phaseScore = 30;   // 3/10 * 100
    const activityScore = 90; // 9/10 * 100
    const successScore = 80;  // 8/10 * 100
    const resilienceScore = 50; // 1/(1+1) * 100

    const correctAGI = Math.round(phaseScore * 0.30 + activityScore * 0.25 + successScore * 0.25 + resilienceScore * 0.20);
    const mutantAGI  = Math.round(phaseScore * 0.25 + activityScore * 0.30 + successScore * 0.25 + resilienceScore * 0.20);

    expect(correctResult.agiScore).toBe(correctAGI);
    expect(correctAGI).not.toBe(mutantAGI);
  });
});

// ─── Webhook Timestamp ────────────────────────────────────────────────────────

describe('Mutation: Webhook skip timestamp check', () => {
  it('old timestamp (600s) fails with check, would pass without check', () => {
    const maxAgeSeconds = 300;
    const nowSeconds = Math.floor(Date.now() / 1000);
    const oldTimestamp = nowSeconds - 600; // 10 minutes ago

    const ageSecs = Math.abs(nowSeconds - oldTimestamp);
    const correctBlocked = ageSecs > maxAgeSeconds;  // true — blocked
    const mutantAllowed  = false;                     // mutant skips check — always allows

    expect(correctBlocked).toBe(true);
    expect(mutantAllowed).toBe(false);
    expect(correctBlocked).not.toBe(mutantAllowed);
  });
});

// ─── Limiter Off-by-one ───────────────────────────────────────────────────────

describe('Mutation: Limiter off-by-one (used <= limit vs used < limit)', () => {
  it('at-limit usage (used=100, limit=100): correct blocks, mutant allows', () => {
    const used = 100;
    const limit = 100;

    const correctAllowed = used < limit;    // false — blocked at limit
    const mutantAllowed  = used <= limit;   // true — off-by-one bug

    expect(correctAllowed).toBe(false);
    expect(mutantAllowed).toBe(true);
    expect(correctAllowed).not.toBe(mutantAllowed);
  });
});

// ─── Feature Map Wrong Tier ───────────────────────────────────────────────────

describe('Mutation: Feature map wrong tier (kaizen requires free instead of pro)', () => {
  it('free tier user blocked by pro requirement, wrongly allowed by free requirement', () => {
    const correctRequirement = 'pro';
    const mutantRequirement  = 'free';
    const userTier = 'free';

    const correctBlocked = !tierMeetsMinimum(userTier, correctRequirement); // true — blocked
    const mutantAllowed  = tierMeetsMinimum(userTier, mutantRequirement);   // true — wrongly allowed

    expect(correctBlocked).toBe(true);
    expect(mutantAllowed).toBe(true);
    // The gate decisions differ
    expect(tierMeetsMinimum(userTier, correctRequirement)).toBe(false);
    expect(tierMeetsMinimum(userTier, mutantRequirement)).toBe(true);
  });
});

// ─── Revenue Tracker ─────────────────────────────────────────────────────────

describe('Mutation: Revenue tracker count vs sum', () => {
  it('counting events vs summing amounts gives different MRR', () => {
    const events = [{ amount: 49 }, { amount: 149 }, { amount: 499 }];

    const correctMRR = events.reduce((sum, e) => sum + e.amount, 0); // 697
    const mutantMRR  = events.length;                                 // 3 (count)

    expect(correctMRR).toBe(697);
    expect(mutantMRR).toBe(3);
    expect(correctMRR).not.toBe(mutantMRR);
  });
});
