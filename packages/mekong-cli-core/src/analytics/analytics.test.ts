/**
 * Analytics test suite — v0.8 ROIaaS Phase 5.
 * Covers: ROICalculator, AgentScorer, RevenueTracker, GrowthAnalyzer, ReportGenerator.
 */
import { describe, it, expect } from 'vitest';
import { ROICalculator, currentMonthPeriod, monthPeriod } from './roi-calculator.js';
import { AgentScorer } from './agent-scorer.js';
import { RevenueTracker } from './revenue-tracker.js';
import { GrowthAnalyzer } from './growth-analyzer.js';
import { ReportGenerator } from './report-generator.js';
import type { AnalyticsPeriod, AgentPerformance, ROIMetrics, RevenueReport, GrowthIndicator } from './types.js';
import type { WebhookEvent } from '../payments/types.js';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makePeriod(label = '2025-03'): AnalyticsPeriod {
  return {
    label,
    startDate: `${label}-01T00:00:00.000Z`,
    endDate: `${label}-31T23:59:59.999Z`,
  };
}

function makeWebhookEvent(overrides: Partial<WebhookEvent> = {}): WebhookEvent {
  return {
    id: `evt-${Math.random().toString(36).slice(2)}`,
    type: 'subscription.active',
    receivedAt: '2025-03-15T12:00:00.000Z',
    processed: true,
    customerId: 'cust-001',
    tier: 'starter',
    ...overrides,
  };
}

// ── ROICalculator ─────────────────────────────────────────────────────────────

describe('ROICalculator', () => {
  const calc = new ROICalculator();
  const period = makePeriod();

  it('calculates positive ROI correctly', () => {
    const result = calc.calculate({
      timeSavedHours: 20,
      hourlyRate: 100,
      revenueGenerated: 500,
      totalCost: 50,
      period,
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    // netValue = 20*100 + 500 - 50 = 2450; ROI = 2450/50 * 100 = 4900%
    expect(result.value.roiPercent).toBe(4900);
    expect(result.value.netValue).toBe(2450);
    expect(result.value.timeSavedValue).toBe(2000);
  });

  it('calculates negative ROI when cost exceeds value', () => {
    const result = calc.calculate({
      timeSavedHours: 0,
      hourlyRate: 100,
      revenueGenerated: 10,
      totalCost: 100,
      period,
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.roiPercent).toBeLessThan(0);
    expect(result.value.netValue).toBe(-90);
  });

  it('handles zero cost (infinite ROI capped to 9999)', () => {
    const result = calc.calculate({
      timeSavedHours: 5,
      hourlyRate: 50,
      revenueGenerated: 0,
      totalCost: 0,
      period,
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.roiPercent).toBe(9999);
  });

  it('handles zero cost and zero value as 0% ROI', () => {
    const result = calc.calculate({ timeSavedHours: 0, hourlyRate: 0, revenueGenerated: 0, totalCost: 0, period });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.roiPercent).toBe(0);
  });

  it('rejects negative hourlyRate', () => {
    const result = calc.calculate({ timeSavedHours: 1, hourlyRate: -1, revenueGenerated: 0, totalCost: 0, period });
    expect(result.ok).toBe(false);
  });

  it('rejects negative timeSavedHours', () => {
    const result = calc.calculate({ timeSavedHours: -1, hourlyRate: 100, revenueGenerated: 0, totalCost: 0, period });
    expect(result.ok).toBe(false);
  });

  it('rejects negative revenueGenerated', () => {
    const result = calc.calculate({ timeSavedHours: 0, hourlyRate: 100, revenueGenerated: -1, totalCost: 0, period });
    expect(result.ok).toBe(false);
  });

  it('rejects negative totalCost', () => {
    const result = calc.calculate({ timeSavedHours: 0, hourlyRate: 100, revenueGenerated: 0, totalCost: -1, period });
    expect(result.ok).toBe(false);
  });

  it('formatSummary includes ROI%', () => {
    const result = calc.calculate({ timeSavedHours: 10, hourlyRate: 100, revenueGenerated: 0, totalCost: 50, period });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const summary = calc.formatSummary(result.value);
    expect(summary).toContain('ROI');
    expect(summary).toContain('%');
  });

  it('produces correct computedAt timestamp', () => {
    const before = new Date().toISOString();
    const result = calc.calculate({ timeSavedHours: 1, hourlyRate: 100, revenueGenerated: 0, totalCost: 10, period });
    const after = new Date().toISOString();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.computedAt >= before).toBe(true);
    expect(result.value.computedAt <= after).toBe(true);
  });
});

describe('monthPeriod / currentMonthPeriod', () => {
  it('currentMonthPeriod returns valid period', () => {
    const p = currentMonthPeriod();
    expect(p.label).toMatch(/^\d{4}-\d{2}$/);
    expect(p.startDate).toContain('T00:00:00');
    expect(p.endDate).toContain('T23:59:59');
  });

  it('monthPeriod(-1) returns prior month', () => {
    const curr = currentMonthPeriod();
    const prev = monthPeriod(-1);
    expect(prev.label < curr.label).toBe(true);
  });

  it('monthPeriod(0) matches currentMonthPeriod', () => {
    const a = monthPeriod(0);
    const b = currentMonthPeriod();
    expect(a.label).toBe(b.label);
  });
});

// ── AgentScorer ───────────────────────────────────────────────────────────────

describe('AgentScorer', () => {
  const scorer = new AgentScorer();

  const perfectInputs = {
    agentName: 'PerfectAgent',
    phasesCompleted: 10,
    totalPhases: 10,
    recentCommits: 10,
    activityBaseline: 10,
    totalExecutions: 100,
    successfulExecutions: 100,
    recoveredExecutions: 0,
    failedExecutions: 0,
  };

  it('scores perfect agent at 100', () => {
    const result = scorer.score(perfectInputs);
    expect(result.agiScore).toBe(100);
    expect(result.successRate).toBe(1);
    expect(result.errorRecoveryRate).toBe(1);
  });

  it('scores zero-activity agent appropriately', () => {
    const result = scorer.score({
      agentName: 'Dormant',
      phasesCompleted: 0,
      totalPhases: 10,
      recentCommits: 0,
      activityBaseline: 10,
      totalExecutions: 0,
      successfulExecutions: 0,
      recoveredExecutions: 0,
      failedExecutions: 0,
    });
    // No executions → success rate = 1, resilience = 1; but phase + activity = 0
    expect(result.agiScore).toBeGreaterThanOrEqual(0);
    expect(result.agiScore).toBeLessThanOrEqual(100);
    expect(result.phaseProgressScore).toBe(0);
    expect(result.activityScore).toBe(0);
  });

  it('applies HIEN-PHAP weights (30/25/25/20)', () => {
    // Phase 50%, activity 50%, success 50%, resilience 50% → score = 50
    const result = scorer.score({
      agentName: 'Half',
      phasesCompleted: 5,
      totalPhases: 10,
      recentCommits: 5,
      activityBaseline: 10,
      totalExecutions: 10,
      successfulExecutions: 5,
      recoveredExecutions: 5,
      failedExecutions: 5,
    });
    expect(result.agiScore).toBe(50);
  });

  it('scoreAll returns sorted descending', () => {
    const results = scorer.scoreAll([
      { ...perfectInputs, agentName: 'A', successfulExecutions: 50, totalExecutions: 100 },
      perfectInputs,
      { ...perfectInputs, agentName: 'B', phasesCompleted: 0, recentCommits: 0 },
    ]);
    expect(results[0].agiScore).toBeGreaterThanOrEqual(results[1].agiScore);
    expect(results[1].agiScore).toBeGreaterThanOrEqual(results[2].agiScore);
  });

  it('clamps agiScore to 0-100', () => {
    const result = scorer.score({ ...perfectInputs, recentCommits: 9999, activityBaseline: 1 });
    expect(result.agiScore).toBeLessThanOrEqual(100);
  });

  it('formatLeaderboard returns table header', () => {
    const perf: AgentPerformance[] = [scorer.score(perfectInputs)];
    const table = scorer.formatLeaderboard(perf);
    expect(table).toContain('AGI Score');
    expect(table).toContain('PerfectAgent');
  });

  it('formatLeaderboard handles empty array', () => {
    const output = scorer.formatLeaderboard([]);
    expect(output).toContain('No agent data');
  });
});

// ── RevenueTracker ────────────────────────────────────────────────────────────

describe('RevenueTracker', () => {
  const tracker = new RevenueTracker();
  const period = makePeriod('2025-03');

  it('computes MRR from active subscriptions', () => {
    const events: WebhookEvent[] = [
      makeWebhookEvent({ tier: 'starter' }),
      makeWebhookEvent({ tier: 'pro', customerId: 'cust-002' }),
      makeWebhookEvent({ tier: 'enterprise', customerId: 'cust-003' }),
    ];
    const result = tracker.buildReport(events, period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    // 1 starter($49) + 1 pro($149) + 1 enterprise($499) = $697
    expect(result.value.mrr).toBe(697);
    expect(result.value.arr).toBe(697 * 12);
    expect(result.value.activeCustomers).toBe(3);
  });

  it('returns zero MRR for empty events', () => {
    const result = tracker.buildReport([], period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.mrr).toBe(0);
    expect(result.value.activeCustomers).toBe(0);
  });

  it('ignores events outside period', () => {
    const outOfPeriod = makeWebhookEvent({ receivedAt: '2025-01-15T12:00:00.000Z', tier: 'pro' });
    const result = tracker.buildReport([outOfPeriod], period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.mrr).toBe(0);
  });

  it('buildFromMRR computes ARR and ARPU', () => {
    const report = tracker.buildFromMRR({
      mrr: 1000,
      activeCustomers: 10,
      tierDistribution: { free: 5, starter: 3, pro: 2, enterprise: 0 },
      period,
    });
    expect(report.arr).toBe(12000);
    expect(report.arpu).toBe(100);
  });

  it('ARPU is 0 when no customers', () => {
    const report = tracker.buildFromMRR({
      mrr: 0, activeCustomers: 0,
      tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 },
      period,
    });
    expect(report.arpu).toBe(0);
  });

  it('formatSummary includes MRR/ARR', () => {
    const report = tracker.buildFromMRR({
      mrr: 500, activeCustomers: 5,
      tierDistribution: { free: 2, starter: 2, pro: 1, enterprise: 0 },
      period,
    });
    const summary = tracker.formatSummary(report);
    expect(summary).toContain('MRR');
    expect(summary).toContain('ARR');
    expect(summary).toContain('500');
  });

  it('tier distribution counts correctly', () => {
    const events: WebhookEvent[] = [
      makeWebhookEvent({ tier: 'starter' }),
      makeWebhookEvent({ tier: 'starter', customerId: 'c2' }),
      makeWebhookEvent({ tier: 'enterprise', customerId: 'c3' }),
    ];
    const result = tracker.buildReport(events, period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.tierDistribution.starter).toBe(2);
    expect(result.value.tierDistribution.enterprise).toBe(1);
    expect(result.value.tierDistribution.pro).toBe(0);
  });
});

// ── GrowthAnalyzer ────────────────────────────────────────────────────────────

describe('GrowthAnalyzer', () => {
  const analyzer = new GrowthAnalyzer();
  const period = makePeriod();

  const baseInputs = {
    period,
    currentMRR: 1000,
    previousMRR: 800,
    currentWeekRevenue: 250,
    previousWeekRevenue: 200,
    startingCustomers: 10,
    newCustomers: 3,
    churnedCustomers: 1,
    expansionRevenue: 100,
  };

  it('computes MoM growth correctly', () => {
    const g = analyzer.analyze(baseInputs);
    // (1000 - 800) / 800 * 100 = 25%
    expect(g.momGrowthPercent).toBe(25);
  });

  it('computes WoW growth correctly', () => {
    const g = analyzer.analyze(baseInputs);
    // (250 - 200) / 200 * 100 = 25%
    expect(g.wowGrowthPercent).toBe(25);
  });

  it('computes churn rate', () => {
    const g = analyzer.analyze(baseInputs);
    // 1 / 10 = 0.1
    expect(g.churnRate).toBe(0.1);
  });

  it('computes NRR', () => {
    const g = analyzer.analyze(baseInputs);
    // (1000 + 100) / 800 * 100 = 137.5%
    expect(g.nrrPercent).toBeCloseTo(137.5, 1);
  });

  it('handles zero previous MRR (no division by zero)', () => {
    const g = analyzer.analyze({ ...baseInputs, previousMRR: 0, previousWeekRevenue: 0 });
    expect(g.momGrowthPercent).toBe(100);
    expect(g.wowGrowthPercent).toBe(100);
    expect(g.nrrPercent).toBe(100);
  });

  it('handles zero starting customers', () => {
    const g = analyzer.analyze({ ...baseInputs, startingCustomers: 0 });
    expect(g.churnRate).toBe(0);
  });

  it('formatSummary includes MoM/WoW', () => {
    const g = analyzer.analyze(baseInputs);
    const summary = analyzer.formatSummary(g);
    expect(summary).toContain('MoM');
    expect(summary).toContain('WoW');
    expect(summary).toContain('+25.0%');
  });

  it('negative growth is reported with minus sign', () => {
    const g = analyzer.analyze({ ...baseInputs, currentMRR: 600, previousMRR: 800 });
    const summary = analyzer.formatSummary(g);
    expect(g.momGrowthPercent).toBeLessThan(0);
    expect(summary).toContain('-25.0%');
  });
});

// ── ReportGenerator ───────────────────────────────────────────────────────────

describe('ReportGenerator', () => {
  const gen = new ReportGenerator();
  const period = makePeriod();

  const scorer = new AgentScorer();
  const tracker = new RevenueTracker();
  const analyzer = new GrowthAnalyzer();
  const calc = new ROICalculator();

  function makeBundle() {
    const roi = calc.calculate({ timeSavedHours: 10, hourlyRate: 100, revenueGenerated: 500, totalCost: 50, period });
    const agents = scorer.scoreAll([{
      agentName: 'TestAgent',
      phasesCompleted: 8, totalPhases: 10,
      recentCommits: 8, activityBaseline: 10,
      totalExecutions: 50, successfulExecutions: 45,
      recoveredExecutions: 3, failedExecutions: 2,
    }]);
    const revenue = tracker.buildFromMRR({
      mrr: 697, activeCustomers: 3,
      tierDistribution: { free: 0, starter: 1, pro: 1, enterprise: 1 },
      period,
    });
    const growth = analyzer.analyze({
      period,
      currentMRR: 697, previousMRR: 500,
      currentWeekRevenue: 175, previousWeekRevenue: 125,
      startingCustomers: 2, newCustomers: 1,
      churnedCustomers: 0, expansionRevenue: 50,
    });
    return { roi: roi.ok ? roi.value : {} as ROIMetrics, agents, revenue, growth };
  }

  it('toMarkdown includes all 4 sections', () => {
    const bundle = makeBundle();
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('## ROI Summary');
    expect(md).toContain('## Agent Leaderboard');
    expect(md).toContain('## Revenue Breakdown');
    expect(md).toContain('## Growth Trends');
  });

  it('toMarkdown includes agent name', () => {
    const bundle = makeBundle();
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('TestAgent');
  });

  it('toMarkdown is valid Markdown (contains table pipes)', () => {
    const bundle = makeBundle();
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('|');
    expect(md).toContain('---');
  });

  it('toCliSummary includes ROI and Revenue sections', () => {
    const bundle = makeBundle();
    const summary = gen.toCliSummary(bundle);
    expect(summary).toContain('ROI');
    expect(summary).toContain('Revenue');
    expect(summary).toContain('Growth');
  });

  it('roiSection shows + sign for positive ROI', () => {
    const bundle = makeBundle();
    const section = gen.roiSection(bundle.roi);
    expect(section).toContain('+');
  });

  it('agentSection handles empty agents', () => {
    const section = gen.agentSection([]);
    expect(section).toContain('no data');
  });

  it('revenueSection shows MRR value', () => {
    const bundle = makeBundle();
    const section = gen.revenueSection(bundle.revenue);
    expect(section).toContain('697');
  });

  it('growthSection shows NRR', () => {
    const bundle = makeBundle();
    const section = gen.growthSection(bundle.growth);
    expect(section).toContain('NRR');
  });
});

// ── Integration ───────────────────────────────────────────────────────────────

describe('Analytics integration', () => {
  it('full pipeline produces consistent results', () => {
    const period = makePeriod('2025-03');
    const calc = new ROICalculator();
    const tracker = new RevenueTracker();
    const analyzer = new GrowthAnalyzer();
    const scorer = new AgentScorer();
    const gen = new ReportGenerator();

    const events: WebhookEvent[] = [
      makeWebhookEvent({ tier: 'pro', customerId: 'c1' }),
      makeWebhookEvent({ tier: 'enterprise', customerId: 'c2' }),
    ];
    const revenueResult = tracker.buildReport(events, period);
    expect(revenueResult.ok).toBe(true);
    const revenue = (revenueResult as { ok: true; value: RevenueReport }).value;

    const roi = calc.calculate({
      timeSavedHours: 20,
      hourlyRate: 100,
      revenueGenerated: revenue.mrr,
      totalCost: 50,
      period,
    });
    expect(roi.ok).toBe(true);

    const growth = analyzer.analyze({
      period,
      currentMRR: revenue.mrr,
      previousMRR: 0,
      currentWeekRevenue: revenue.mrr / 4,
      previousWeekRevenue: 0,
      startingCustomers: 0,
      newCustomers: 2,
      churnedCustomers: 0,
      expansionRevenue: 0,
    });

    const agents = scorer.scoreAll([{
      agentName: 'Worker',
      phasesCompleted: 5, totalPhases: 7,
      recentCommits: 5, activityBaseline: 10,
      totalExecutions: 20, successfulExecutions: 18,
      recoveredExecutions: 1, failedExecutions: 1,
    }]);

    const bundle = { roi: (roi as { ok: true; value: ROIMetrics }).value, agents, revenue, growth };
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('# Mekong Analytics Report');
    expect(md).toContain('Worker');
    // MRR: 149 + 499 = 648
    expect(revenue.mrr).toBe(648);
    expect(growth.momGrowthPercent).toBe(100); // from 0 → positive
  });

  it('zero-data pipeline produces valid (zero) bundle', () => {
    const period = makePeriod();
    const calc = new ROICalculator();
    const tracker = new RevenueTracker();
    const analyzer = new GrowthAnalyzer();
    const scorer = new AgentScorer();
    const gen = new ReportGenerator();

    const revenue = tracker.buildFromMRR({ mrr: 0, activeCustomers: 0, tierDistribution: { free: 0, starter: 0, pro: 0, enterprise: 0 }, period });
    const roiResult = calc.calculate({ timeSavedHours: 0, hourlyRate: 100, revenueGenerated: 0, totalCost: 0, period });
    const roi = (roiResult as { ok: true; value: ROIMetrics }).value;
    const growth = analyzer.analyze({ period, currentMRR: 0, previousMRR: 0, currentWeekRevenue: 0, previousWeekRevenue: 0, startingCustomers: 0, newCustomers: 0, churnedCustomers: 0, expansionRevenue: 0 });
    const agents: AgentPerformance[] = [];
    const bundle = { roi, agents, revenue, growth };
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('## ROI Summary');
    expect(md).not.toContain('undefined');
    expect(md).not.toContain('NaN');
  });

  it('GrowthIndicator passes through computedAt timestamp', () => {
    const period = makePeriod();
    const g = new GrowthAnalyzer().analyze({
      period, currentMRR: 0, previousMRR: 0,
      currentWeekRevenue: 0, previousWeekRevenue: 0,
      startingCustomers: 0, newCustomers: 0,
      churnedCustomers: 0, expansionRevenue: 0,
    });
    expect(g.computedAt).toMatch(/^\d{4}-\d{2}-\d{2}/);
  });

  it('AgentPerformance computedAt is recent', () => {
    const scorer = new AgentScorer();
    const perf = scorer.score({
      agentName: 'A', phasesCompleted: 1, totalPhases: 1,
      recentCommits: 1, activityBaseline: 1,
      totalExecutions: 1, successfulExecutions: 1,
      recoveredExecutions: 0, failedExecutions: 0,
    });
    const diff = Date.now() - new Date(perf.computedAt).getTime();
    expect(diff).toBeLessThan(5000);
  });

  it('revenue tier distribution sums match activeCustomers', () => {
    const period = makePeriod();
    const events: WebhookEvent[] = [
      makeWebhookEvent({ tier: 'starter', customerId: 'c1' }),
      makeWebhookEvent({ tier: 'pro', customerId: 'c2' }),
      makeWebhookEvent({ tier: 'pro', customerId: 'c3' }),
    ];
    const result = new RevenueTracker().buildReport(events, period);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { tierDistribution, activeCustomers } = result.value;
    const tierSum = tierDistribution.starter + tierDistribution.pro + tierDistribution.enterprise;
    expect(tierSum).toBe(activeCustomers);
  });
});
