/**
 * Statistical Analyzer — finds bottlenecks, trends, and anomalies.
 * Uses simple-statistics for percentiles, regression, correlation.
 */
import type { SopAnalytics, AgentAnalytics, Bottleneck } from './types.js';
import type { MetricsCollector } from './collector.js';
import {
  nowRange,
  safeMean,
  safeMedian,
  safeP95,
  calcTrend,
  deriveTrend,
  buildStepAnalytics,
  detectSeriesAnomalies,
  collectBottlenecks,
} from './analyzer-stats.js';

export class KaizenAnalyzer {
  constructor(private readonly collector: MetricsCollector) {}

  /** Analyze SOP performance over a period */
  async analyzeSop(sopName: string, days: number): Promise<SopAnalytics> {
    const { from, to } = nowRange(days);
    const halfFrom = new Date(new Date(from).getTime() - days * 24 * 60 * 60 * 1000).toISOString();

    const [durSeries, sucSeries, costSeries, prevDurSeries, prevSucSeries, prevCostSeries] =
      await Promise.all([
        this.collector.query('sop.step.duration', from, to, { sop: sopName }),
        this.collector.query('sop.step.success', from, to, { sop: sopName }),
        this.collector.query('sop.step.cost', from, to, { sop: sopName }),
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

    const stepAnalytics = buildStepAnalytics(durSeries, sucSeries, costSeries, durations, costs);
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
    return collectBottlenecks(this.collector, from, to);
  }

  /** Detect anomalies (sudden changes from baseline) */
  async detectAnomalies(metric: string, days: number) {
    const { from, to } = nowRange(days);
    const series = await this.collector.query(metric, from, to);
    return detectSeriesAnomalies(series);
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

    const pct = (points: typeof sopSuc.points) =>
      points.length === 0 ? 100 : (points.filter(p => p.value === 1).length / points.length) * 100;

    const sopScore = pct(sopSuc.points);
    const agentScore = pct(agentSuc.points);
    const toolScore = pct(toolSuc.points);
    const score = Math.round(sopScore * 0.45 + agentScore * 0.3 + toolScore * 0.25);
    const diff = score - pct(prevSopSuc.points);
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
