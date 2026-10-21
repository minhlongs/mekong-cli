/**
 * Kaizen Statistical Helpers — Pure statistical and step analytics helpers.
 */
import { randomUUID } from 'crypto';
import { mean, median, standardDeviation, quantile } from 'simple-statistics';
import type { StepAnalytics, MetricSeries, Bottleneck } from './types.js';
import type { MetricsCollector } from './collector.js';

export function nowRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to.getTime() - days * 24 * 60 * 60 * 1000);
  return { from: from.toISOString(), to: to.toISOString() };
}

export function safeMean(values: number[]): number {
  return values.length > 0 ? mean(values) : 0;
}

export function safeMedian(values: number[]): number {
  return values.length > 0 ? median(values) : 0;
}

export function safeP95(values: number[]): number {
  return values.length > 0 ? quantile(values, 0.95) : 0;
}

export function calcTrend(current: number, previous: number): number {
  if (previous === 0) return 0;
  return Math.round(((current - previous) / previous) * 100);
}

export function deriveTrend(durationTrend: number, successTrend: number): 'improving' | 'stable' | 'degrading' {
  if (successTrend > 2 || durationTrend < -5) return 'improving';
  if (successTrend < -2 || durationTrend > 10) return 'degrading';
  return 'stable';
}

export function buildStepAnalytics(
  durSeries: MetricSeries,
  sucSeries: MetricSeries,
  costSeries: MetricSeries,
  durations: number[],
  costs: number[],
): StepAnalytics[] {
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
      isBottleneck: false,
      percentOfTotal: totalDur > 0 ? (totalStepDur / totalDur) * 100 : 0,
      retryRate: 0,
      costContribution: costs.length > 0
        ? (safeMean(stepCosts) / (safeMean(costs) || 1)) * 100 : 0,
    });
  }

  if (stepAnalytics.length > 0) {
    const slowest = stepAnalytics.reduce((a, b) => a.percentOfTotal > b.percentOfTotal ? a : b);
    slowest.isBottleneck = true;
  }

  return stepAnalytics;
}

export function detectSeriesAnomalies(series: MetricSeries): Array<{
  timestamp: string;
  value: number;
  expected: number;
  deviation: number;
  severity: 'low' | 'medium' | 'high';
}> {
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

export async function collectBottlenecks(
  collector: MetricsCollector,
  from: string,
  to: string,
): Promise<Bottleneck[]> {
  const bottlenecks: Bottleneck[] = [];
  const now = new Date().toISOString();

  const [toolDur, toolSuc, agentSuc] = await Promise.all([
    collector.query('tool.call.duration', from, to),
    collector.query('tool.call.success', from, to),
    collector.query('agent.task.success', from, to),
  ]);

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

  const rank = { critical: 4, high: 3, medium: 2, low: 1 };
  return bottlenecks.sort((a, b) => rank[b.impact] - rank[a.impact]);
}
