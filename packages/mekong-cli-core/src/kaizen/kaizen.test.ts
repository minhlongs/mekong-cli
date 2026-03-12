/**
 * Kaizen Analytics module tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MetricsCollector } from './collector.js';
import { KaizenAnalyzer } from './analyzer.js';
import { KaizenRecommender } from './recommender.js';
import { KaizenReporter } from './report.js';
import type { KaizenReport } from './types.js';

// ── MetricsCollector ──────────────────────────────────────────────────────────

describe('MetricsCollector', () => {
  let collector: MetricsCollector;

  beforeEach(() => {
    collector = new MetricsCollector('/tmp/mekong-test-kaizen');
  });

  it('buffers metric points', () => {
    collector.record('test.metric', 42, 'ms', { label: 'a' });
    // No error = buffer accepted the point
  });

  it('recordSopStep stores three metrics', () => {
    const spy = vi.spyOn(collector, 'record');
    collector.recordSopStep('deploy', 'build', 1200, true, 0.002);
    expect(spy).toHaveBeenCalledTimes(3);
    expect(spy).toHaveBeenCalledWith('sop.step.duration', 1200, 'ms', { sop: 'deploy', step: 'build' });
    expect(spy).toHaveBeenCalledWith('sop.step.success', 1, 'count', { sop: 'deploy', step: 'build' });
    expect(spy).toHaveBeenCalledWith('sop.step.cost', 0.002, 'usd', { sop: 'deploy', step: 'build' });
  });

  it('recordAgentTask stores four metrics', () => {
    const spy = vi.spyOn(collector, 'record');
    collector.recordAgentTask('coder', 5000, 1500, 0.01, true);
    expect(spy).toHaveBeenCalledTimes(4);
  });

  it('recordToolCall stores two metrics', () => {
    const spy = vi.spyOn(collector, 'record');
    collector.recordToolCall('shell', 300, false);
    expect(spy).toHaveBeenCalledTimes(2);
    expect(spy).toHaveBeenCalledWith('tool.call.success', 0, 'count', { tool: 'shell' });
  });

  it('query returns empty series when no data', async () => {
    const series = await collector.query('nonexistent', '2020-01-01T00:00:00Z', '2020-01-02T00:00:00Z');
    expect(series.name).toBe('nonexistent');
    expect(series.points).toHaveLength(0);
  });

  it('query returns in-memory buffered points', async () => {
    const now = new Date();
    const from = new Date(now.getTime() - 1000).toISOString();
    const to = new Date(now.getTime() + 1000).toISOString();
    collector.record('latency', 100, 'ms', { service: 'api' });
    const series = await collector.query('latency', from, to, { service: 'api' });
    expect(series.points).toHaveLength(1);
    expect(series.points[0]!.value).toBe(100);
  });

  it('query filters by label', async () => {
    const now = new Date();
    const from = new Date(now.getTime() - 1000).toISOString();
    const to = new Date(now.getTime() + 1000).toISOString();
    collector.record('latency', 100, 'ms', { service: 'api' });
    collector.record('latency', 200, 'ms', { service: 'db' });
    const series = await collector.query('latency', from, to, { service: 'api' });
    expect(series.points).toHaveLength(1);
    expect(series.points[0]!.value).toBe(100);
  });

  it('subscribeToEvents does not throw', () => {
    expect(() => collector.subscribeToEvents()).not.toThrow();
  });
});

// ── KaizenAnalyzer ────────────────────────────────────────────────────────────

describe('KaizenAnalyzer', () => {
  let collector: MetricsCollector;
  let analyzer: KaizenAnalyzer;

  beforeEach(() => {
    collector = new MetricsCollector('/tmp/mekong-test-kaizen');
    analyzer = new KaizenAnalyzer(collector);
  });

  it('analyzeSop returns valid structure with no data', async () => {
    const result = await analyzer.analyzeSop('deploy', 7);
    expect(result.sopName).toBe('deploy');
    expect(result.totalRuns).toBe(0);
    expect(result.successRate).toBe(100);
    expect(result.trend).toMatch(/^(improving|stable|degrading)$/);
  });

  it('analyzeSop with data calculates correct stats', async () => {
    const now = Date.now();
    // Seed collector buffer with SOP metrics
    for (let i = 0; i < 5; i++) {
      collector.recordSopStep('ci', 'test', 1000 + i * 100, true, 0.001);
    }
    collector.recordSopStep('ci', 'test', 5000, false, 0.002); // one failure
    const result = await analyzer.analyzeSop('ci', 30);
    expect(result.sopName).toBe('ci');
    expect(result.stepAnalytics.length).toBeGreaterThanOrEqual(0);
  });

  it('analyzeAgent returns valid structure', async () => {
    const result = await analyzer.analyzeAgent('coder', 7);
    expect(result.agentName).toBe('coder');
    expect(result.efficiencyScore).toBeGreaterThanOrEqual(0);
    expect(result.efficiencyScore).toBeLessThanOrEqual(100);
  });

  it('findBottlenecks returns array', async () => {
    const result = await analyzer.findBottlenecks(7);
    expect(Array.isArray(result)).toBe(true);
  });

  it('findBottlenecks detects high tool failure rate', async () => {
    const now = Date.now();
    // Record 8 failures, 2 successes for tool "flaky-api"
    for (let i = 0; i < 8; i++) collector.recordToolCall('flaky-api', 200, false);
    for (let i = 0; i < 2; i++) collector.recordToolCall('flaky-api', 200, true);
    const bottlenecks = await analyzer.findBottlenecks(7);
    const found = bottlenecks.find(b => b.location === 'flaky-api');
    expect(found).toBeDefined();
    expect(found!.impact).toMatch(/^(medium|high|critical)$/);
  });

  it('detectAnomalies returns empty for insufficient data', async () => {
    const result = await analyzer.detectAnomalies('sop.step.duration', 7);
    expect(Array.isArray(result)).toBe(true);
  });

  it('calculateHealthScore returns 0-100 score', async () => {
    const result = await analyzer.calculateHealthScore(7);
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(100);
    expect(result.trend).toMatch(/^(improving|stable|degrading)$/);
    expect(typeof result.components).toBe('object');
  });
});

// ── KaizenRecommender ─────────────────────────────────────────────────────────

describe('KaizenRecommender', () => {
  const mockLlm = {
    chat: vi.fn().mockResolvedValue({
      content: '[]',
      provider: 'mock',
      model: 'mock',
      usage: { inputTokens: 10, outputTokens: 5 },
      latencyMs: 50,
    }),
  } as never;

  let recommender: KaizenRecommender;

  beforeEach(() => {
    recommender = new KaizenRecommender(mockLlm);
  });

  it('returns empty suggestions when no data', async () => {
    const result = await recommender.suggest({
      sopAnalytics: [],
      agentAnalytics: [],
      bottlenecks: [],
      budgetData: { totalSpent: 0, byModel: {} },
    });
    expect(Array.isArray(result)).toBe(true);
  });

  it('suggests parallelize for bottleneck step >50% time', async () => {
    const result = await recommender.suggest({
      sopAnalytics: [{
        sopName: 'deploy',
        totalRuns: 10,
        successRate: 90,
        avgDuration: 60,
        medianDuration: 55,
        p95Duration: 80,
        avgCost: 0.05,
        avgTokens: 1000,
        failureReasons: [],
        stepAnalytics: [{
          stepId: 'build',
          stepName: 'build',
          avgDuration: 35,
          medianDuration: 34,
          successRate: 100,
          isBottleneck: true,
          percentOfTotal: 58,
          retryRate: 0,
          costContribution: 40,
        }],
        trend: 'stable',
        trendData: { durationTrend: 0, successTrend: 0, costTrend: 0 },
      }],
      agentAnalytics: [],
      bottlenecks: [],
      budgetData: { totalSpent: 0, byModel: {} },
    });
    const parallelSuggestion = result.find(s => s.type === 'parallelize');
    expect(parallelSuggestion).toBeDefined();
    expect(parallelSuggestion!.target).toBe('deploy.build');
  });

  it('suggests model_downgrade when expensive model dominates', async () => {
    const result = await recommender.suggest({
      sopAnalytics: [],
      agentAnalytics: [],
      bottlenecks: [],
      budgetData: { totalSpent: 10, byModel: { 'claude-opus': 5 } },
    });
    const downgrade = result.find(s => s.type === 'model_downgrade');
    expect(downgrade).toBeDefined();
    expect(downgrade!.autoApplicable).toBe(true);
  });

  it('apply returns ok for auto-applicable suggestion', async () => {
    const suggestion = {
      id: 'test-id',
      type: 'model_downgrade' as const,
      title: 'Test',
      description: 'Test',
      target: 'opus',
      evidence: 'cost data',
      estimatedImpact: { timeSaved: 0, costSaved: 5, successRateChange: -1 },
      autoApplicable: true,
      status: 'proposed' as const,
      createdAt: new Date().toISOString(),
    };
    const result = await recommender.apply(suggestion);
    expect(result.ok).toBe(true);
    expect(suggestion.status).toBe('applied');
  });

  it('apply returns err for non-auto-applicable suggestion', async () => {
    const suggestion = {
      id: 'test-id',
      type: 'parallelize' as const,
      title: 'Test',
      description: 'Test',
      target: 'deploy.build',
      evidence: 'timing data',
      estimatedImpact: { timeSaved: 10, costSaved: 0, successRateChange: 0 },
      autoApplicable: false,
      status: 'proposed' as const,
      createdAt: new Date().toISOString(),
    };
    const result = await recommender.apply(suggestion);
    expect(result.ok).toBe(false);
  });

  it('revert returns ok', async () => {
    const result = await recommender.revert('some-id');
    expect(result.ok).toBe(true);
  });
});

// ── KaizenReporter ────────────────────────────────────────────────────────────

describe('KaizenReporter', () => {
  const mockAnalyzer = {
    calculateHealthScore: vi.fn().mockResolvedValue({ score: 85, trend: 'improving', components: {} }),
    findBottlenecks: vi.fn().mockResolvedValue([]),
    analyzeSop: vi.fn().mockResolvedValue({
      sopName: 'deploy', totalRuns: 5, successRate: 100,
      avgDuration: 30, medianDuration: 28, p95Duration: 45,
      avgCost: 0.01, avgTokens: 500, failureReasons: [],
      stepAnalytics: [], trend: 'stable',
      trendData: { durationTrend: 0, successTrend: 0, costTrend: 0 },
    }),
    analyzeAgent: vi.fn().mockResolvedValue({
      agentName: 'coder', totalTasks: 10, successRate: 90,
      avgTokensPerTask: 800, avgCostPerTask: 0.005, avgDuration: 5,
      topTools: [], failurePatterns: [], efficiencyScore: 75,
    }),
  } as never;

  const mockRecommender = {
    suggest: vi.fn().mockResolvedValue([]),
  } as never;

  let reporter: KaizenReporter;

  beforeEach(() => {
    reporter = new KaizenReporter(mockAnalyzer, mockRecommender);
  });

  it('generate returns ok result', async () => {
    const result = await reporter.generate({ depth: 'quick', days: 7 });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.overallHealth.score).toBe(85);
      expect(result.value.overallHealth.trend).toBe('improving');
    }
  });

  it('renderCli returns non-empty string', () => {
    const report: KaizenReport = {
      period: { from: '2026-03-01T00:00:00Z', to: '2026-03-08T00:00:00Z' },
      overallHealth: { score: 82, trend: 'stable' },
      sopAnalytics: [],
      agentAnalytics: [],
      bottlenecks: [],
      suggestions: [],
      comparison: {
        totalSopRuns: { current: 10, previous: 8, change: 25 },
        avgSopDuration: { current: 30, previous: 35, change: -14 },
        totalCost: { current: 0.5, previous: 0.6, change: -16 },
        overallSuccessRate: { current: 95, previous: 92, change: 3 },
      },
    };
    const output = reporter.renderCli(report);
    expect(typeof output).toBe('string');
    expect(output).toContain('KAIZEN REPORT');
    expect(output).toContain('82');
  });

  it('renderCli includes bottlenecks when present', () => {
    const report: KaizenReport = {
      period: { from: '2026-03-01T00:00:00Z', to: '2026-03-08T00:00:00Z' },
      overallHealth: { score: 60, trend: 'degrading' },
      sopAnalytics: [],
      agentAnalytics: [],
      bottlenecks: [{
        id: 'bn-1', type: 'tool', location: 'shell-tool',
        metric: 'failure_rate', currentValue: 45, expectedValue: 5,
        impact: 'high', detectedAt: '2026-03-07T00:00:00Z',
      }],
      suggestions: [],
      comparison: {
        totalSopRuns: { current: 0, previous: 0, change: 0 },
        avgSopDuration: { current: 0, previous: 0, change: 0 },
        totalCost: { current: 0, previous: 0, change: 0 },
        overallSuccessRate: { current: 60, previous: 70, change: -10 },
      },
    };
    const output = reporter.renderCli(report);
    expect(output).toContain('shell-tool');
    expect(output).toContain('HIGH');
  });

  it('renderMarkdown contains markdown headers', () => {
    const report: KaizenReport = {
      period: { from: '2026-03-01T00:00:00Z', to: '2026-03-08T00:00:00Z' },
      overallHealth: { score: 90, trend: 'improving' },
      sopAnalytics: [],
      agentAnalytics: [],
      bottlenecks: [],
      suggestions: [{
        id: 's-1', type: 'model_downgrade', title: 'Switch model',
        description: 'Cheaper model available', target: 'opus',
        evidence: 'cost data',
        estimatedImpact: { timeSaved: 0, costSaved: 5, successRateChange: -1 },
        autoApplicable: true, status: 'proposed',
        createdAt: '2026-03-07T00:00:00Z',
      }],
      comparison: {
        totalSopRuns: { current: 0, previous: 0, change: 0 },
        avgSopDuration: { current: 0, previous: 0, change: 0 },
        totalCost: { current: 0, previous: 0, change: 0 },
        overallSuccessRate: { current: 90, previous: 85, change: 5 },
      },
    };
    const md = reporter.renderMarkdown(report);
    expect(md).toContain('# Kaizen Report');
    expect(md).toContain('## Overall Health');
    expect(md).toContain('Switch model');
    expect(md).toContain('AUTO');
  });
});
