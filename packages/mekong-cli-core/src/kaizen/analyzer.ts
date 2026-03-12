/**
 * Statistical Analyzer — finds bottlenecks, trends, and anomalies.
 * Uses simple-statistics for percentiles, regression, correlation.
 */
import { mean, median, standardDeviation, linearRegression, quantile } from 'simple-statistics';
import type { SopAnalytics, StepAnalytics, AgentAnalytics, Bottleneck } from './types.js';
import type { MetricsCollector } from './collector.js';
import { randomUUID } from 'crypto';

function nowRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to.getTime() - days * 24 * 60 * 60 * 1000);
  return { from: from.toISOString(), to: to.toISOString() };
}

function safeMean(values: number[]): number {
  return values.length > 0 ? mean(values) : 0;
}
function safeMedian(values: number[]): number {
  return values.length > 0 ? median(values) : 0;
}
function safeP95(values: number[]): number {
  return values.length > 0 ? quantile(values, 0.95) : 0;
}

function calcTrend(current: number, previous: number): number {
  if (previous === 0) return 0;
  return Math.round(((current - previous) / previous) * 100);
}

function deriveTrend(durationTrend: number, successTrend: number): 'improving' | 'stable' | 'degrading' {
  if (successTrend > 2 || durationTrend < -5) return 'improving';
  if (successTrend < -2 || durationTrend > 10) return 'degrading';
  return 'stable';
}

export class KaizenAnalyzer {
  constructor(private readonly collector: MetricsCollector) {}

  /** Analyze SOP performance over a period */
  async analyzeSop(sopName: string, days: number): Promise<SopAnalytics> {
    const { from, to } = nowRange(days);
    const halfFrom = new Date(new Date(from).getTime() - days * 24 * 60 * 60 * 1000).toISOString();

    const [durSeries, sucSeries, costSeries] = await Promise.all([
      this.collector.query('sop.step.duration', from, to, { sop: sopName }),
      this.collector.query('sop.step.success', from, to, { sop: sopName }),
      this.collector.query('sop.step.cost', from, to, { sop: sopName }),
    ]);
    const [prevDurSeries, prevSucSeries, prevCostSeries] = await Promise.all([
      this.collector.query('sop.step.duration', halfFrom, from, { sop: sopName }),
      this.collector.query('sop.step.success', halfFrom, from, { sop: sopName }),
      this.collector.query('sop.step.cost', halfFrom, from, { sop: sopName }),
    ]);

    const durations = durSeries.points.map(p => p.value);
    const successes = sucSeries.points.map(p => p.value);
    const costs = costSeries.points.map(p => p.value);
    const prevDurations = prevDurSeries.points.map(p => p.value);
    const prevSuccesses = prevSucSeries.points.map(p => p.value);
    const prevCosts = prevCostSeries.points.map(p => p.value);

    const totalRuns = successes.length;
    const successRate = totalRuns > 0 ? (successes.filter(v => v === 1).length / totalRuns) * 100 : 100;
    const prevSuccessRate = prevSuccesses.length > 0
      ? (prevSuccesses.filter(v => v === 1).length / prevSuccesses.length) * 100 : 100;

    // Gather unique step IDs
    const stepIds = [...new Set(durSeries.points.map(p => p.labels['step']).filter(Boolean))];
    const stepAnalytics: StepAnalytics[] = [];
    const totalDur = safeMean(durations) * durations.length || 1;

    for (const stepId of stepIds) {
      const stepDurs = durSeries.points.filter(p => p.labels['step'] === stepId).map(p => p.value);
      const stepSucs = sucSeries.points.filter(p => p.labels['step'] === stepId).map(p => p.value);
      const stepCosts = costSeries.points.filter(p => p.labels['step'] === stepId).map(p => p.value);
      const stepMeanDur = safeMean(stepDurs);
      const stepSuccessRate = stepSucs.length > 0
        ? (stepSucs.filter(v => v === 1).length / stepSucs.length) * 100 : 100;
      const totalStepDur = stepMeanDur * stepDurs.length;

      stepAnalytics.push({
        stepId,
        stepName: stepId,
        avgDuration: stepMeanDur,
        medianDuration: safeMedian(stepDurs),
        successRate: stepSuccessRate,
        isBottleneck: false, // will mark after all steps computed
        percentOfTotal: totalDur > 0 ? (totalStepDur / totalDur) * 100 : 0,
        retryRate: 0,
        costContribution: costs.length > 0
          ? (safeMean(stepCosts) / (safeMean(costs) || 1)) * 100 : 0,
      });
    }

    // Mark bottleneck — step with highest percentOfTotal or lowest successRate
    if (stepAnalytics.length > 0) {
      const slowest = stepAnalytics.reduce((a, b) => a.percentOfTotal > b.percentOfTotal ? a : b);
      slowest.isBottleneck = true;
    }

    const durationTrend = calcTrend(safeMean(durations), safeMean(prevDurations));
    const successTrend = calcTrend(successRate, prevSuccessRate);
    const costTrend = calcTrend(safeMean(costs), safeMean(prevCosts));

    return {
      sopName,
      totalRuns,
      successRate,
      avgDuration: safeMean(durations) / 1000,
      medianDuration: safeMedian(durations) / 1000,
      p95Duration: safeP95(durations) / 1000,
      avgCost: safeMean(costs),
      avgTokens: 0,
      failureReasons: [],
      stepAnalytics,
      trend: deriveTrend(durationTrend, successTrend),
      trendData: { durationTrend, successTrend, costTrend },
    };
  }

  /** Analyze agent performance */
  async analyzeAgent(agentName: string, days: number): Promise<AgentAnalytics> {
    const { from, to } = nowRange(days);

    const [durSeries, sucSeries, tokenSeries, costSeries] = await Promise.all([
      this.collector.query('agent.task.duration', from, to, { agent: agentName }),
      this.collector.query('agent.task.success', from, to, { agent: agentName }),
      this.collector.query('agent.task.tokens', from, to, { agent: agentName }),
      this.collector.query('agent.task.cost', from, to, { agent: agentName }),
    ]);

    const durations = durSeries.points.map(p => p.value);
    const successes = sucSeries.points.map(p => p.value);
    const tokens = tokenSeries.points.map(p => p.value);
    const costs = costSeries.points.map(p => p.value);

    const totalTasks = successes.length;
    const successRate = totalTasks > 0
      ? (successes.filter(v => v === 1).length / totalTasks) * 100 : 100;
    const avgTokensPerTask = safeMean(tokens);
    const avgCostPerTask = safeMean(costs);

    // Efficiency score: 0-100 composite
    const efficiencyScore = Math.min(100, Math.max(0,
      successRate * 0.5 +
      (avgTokensPerTask < 2000 ? 30 : avgTokensPerTask < 5000 ? 15 : 0) +
      (safeMean(durations) < 5000 ? 20 : safeMean(durations) < 30000 ? 10 : 0),
    ));

    return {
      agentName,
      totalTasks,
      successRate,
      avgTokensPerTask,
      avgCostPerTask,
      avgDuration: safeMean(durations) / 1000,
      topTools: [],
      failurePatterns: [],
      efficiencyScore,
    };
  }

  /** Find all bottlenecks across the system */
  async findBottlenecks(days: number): Promise<Bottleneck[]> {
    const { from, to } = nowRange(days);
    const bottlenecks: Bottleneck[] = [];
    const now = new Date().toISOString();

    // Check tool failures
    const toolDur = await this.collector.query('tool.call.duration', from, to);
    const toolSuc = await this.collector.query('tool.call.success', from, to);

    const toolIds = [...new Set(toolDur.points.map(p => p.labels['tool']).filter(Boolean))];
    for (const tool of toolIds) {
      const suc = toolSuc.points.filter(p => p.labels['tool'] === tool).map(p => p.value);
      if (suc.length === 0) continue;
      const failRate = (suc.filter(v => v === 0).length / suc.length) * 100;
      if (failRate > 20) {
        bottlenecks.push({
          id: randomUUID(),
          type: 'tool',
          location: tool,
          metric: 'failure_rate',
          currentValue: failRate,
          expectedValue: 5,
          impact: failRate > 50 ? 'critical' : failRate > 35 ? 'high' : 'medium',
          detectedAt: now,
        });
      }
    }

    // Check agent efficiency
    const agentSuc = await this.collector.query('agent.task.success', from, to);
    const agentIds = [...new Set(agentSuc.points.map(p => p.labels['agent']).filter(Boolean))];
    for (const agent of agentIds) {
      const suc = agentSuc.points.filter(p => p.labels['agent'] === agent).map(p => p.value);
      if (suc.length === 0) continue;
      const failRate = (suc.filter(v => v === 0).length / suc.length) * 100;
      if (failRate > 15) {
        bottlenecks.push({
          id: randomUUID(),
          type: 'agent',
          location: agent,
          metric: 'failure_rate',
          currentValue: failRate,
          expectedValue: 5,
          impact: failRate > 40 ? 'high' : 'medium',
          detectedAt: now,
        });
      }
    }

    return bottlenecks.sort((a, b) => {
      const rank = { critical: 4, high: 3, medium: 2, low: 1 };
      return rank[b.impact] - rank[a.impact];
    });
  }

  /** Detect anomalies (sudden changes from baseline) */
  async detectAnomalies(metric: string, days: number): Promise<Array<{
    timestamp: string;
    value: number;
    expected: number;
    deviation: number;
    severity: 'low' | 'medium' | 'high';
  }>> {
    const { from, to } = nowRange(days);
    const series = await this.collector.query(metric, from, to);
    if (series.points.length < 5) return [];

    const values = series.points.map(p => p.value);
    const mu = mean(values);
    const sigma = standardDeviation(values);
    if (sigma === 0) return [];

    return series.points
      .map(p => {
        const deviation = Math.abs(p.value - mu) / sigma;
        if (deviation < 2) return null;
        const severity: 'low' | 'medium' | 'high' =
          deviation >= 4 ? 'high' : deviation >= 3 ? 'medium' : 'low';
        return { timestamp: p.timestamp, value: p.value, expected: mu, deviation, severity };
      })
      .filter((x): x is NonNullable<typeof x> => x !== null);
  }

  /** Calculate system-wide health score (0-100) */
  async calculateHealthScore(days: number): Promise<{
    score: number;
    components: Record<string, number>;
    trend: 'improving' | 'stable' | 'degrading';
  }> {
    const { from, to } = nowRange(days);
    const halfFrom = new Date(new Date(from).getTime() - days * 24 * 60 * 60 * 1000).toISOString();

    const [sopSuc, agentSuc, toolSuc, prevSopSuc] = await Promise.all([
      this.collector.query('sop.step.success', from, to),
      this.collector.query('agent.task.success', from, to),
      this.collector.query('tool.call.success', from, to),
      this.collector.query('sop.step.success', halfFrom, from),
    ]);

    const pct = (points: typeof sopSuc.points) => {
      if (points.length === 0) return 100;
      return (points.filter(p => p.value === 1).length / points.length) * 100;
    };

    const sopScore = pct(sopSuc.points);
    const agentScore = pct(agentSuc.points);
    const toolScore = pct(toolSuc.points);

    const score = Math.round(sopScore * 0.45 + agentScore * 0.3 + toolScore * 0.25);

    const prevSopScore = pct(prevSopSuc.points);
    const diff = score - prevSopScore;
    const trend: 'improving' | 'stable' | 'degrading' =
      diff > 3 ? 'improving' : diff < -3 ? 'degrading' : 'stable';

    return {
      score,
      components: {
        sop_success_rate: sopScore,
        agent_success_rate: agentScore,
        tool_reliability: toolScore,
      },
      trend,
    };
  }
}
