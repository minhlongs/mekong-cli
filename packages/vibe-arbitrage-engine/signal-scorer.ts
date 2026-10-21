/**
 * ArbitrageSignalScorer — Multi-factor confidence scoring for arbitrage opportunities.
 */

import {
  SignalFactors, ScoredSignal, FactorScores, ScorerConfig,
  DEFAULT_SCORER_WEIGHTS, DEFAULT_SCORER_CONFIG,
} from './signal-scorer-types';

export * from './signal-scorer-types';

export class ArbitrageSignalScorer {
  private config: ScorerConfig;
  private scoringHistory: ScoredSignal[] = [];

  constructor(config?: Partial<ScorerConfig>) {
    this.config = {
      ...DEFAULT_SCORER_CONFIG,
      ...config,
      weights: { ...DEFAULT_SCORER_WEIGHTS, ...config?.weights },
    };
  }

  score(factors: SignalFactors): ScoredSignal {
    if (!factors.fillable || !factors.exchangeHealthy) {
      const signal = this.disqualifiedSignal(factors);
      this.scoringHistory.push(signal);
      return signal;
    }

    const scores: FactorScores = {
      spread: this.scoreSpread(factors.spreadPercent),
      profitability: this.scoreProfitability(factors.netProfitPercent),
      liquidity: factors.liquidityScore,
      latency: this.scoreLatency(factors.latencyMs),
      feeCost: this.scoreFeeCost(factors.feeCostPercent),
      pattern: this.scorePattern(factors.spreadZScore),
    };

    const w = this.config.weights;
    const totalScore = Math.round(
      scores.spread * w.spread +
      scores.profitability * w.profitability +
      scores.liquidity * w.liquidity +
      scores.latency * w.latency +
      scores.feeCost * w.feeCost +
      scores.pattern * w.pattern
    );

    const grade = this.letterGrade(totalScore);
    const recommendation = this.recommend(totalScore);
    const reason = this.buildReason(scores, totalScore, grade);

    const signal: ScoredSignal = { factors, scores, totalScore, grade, recommendation, reason };
    this.scoringHistory.push(signal);
    return signal;
  }

  private scoreSpread(spreadPercent: number): number {
    if (spreadPercent <= this.config.minSpreadPercent) return 0;
    if (spreadPercent >= this.config.maxSpreadPercent) return 100;
    const range = this.config.maxSpreadPercent - this.config.minSpreadPercent;
    return Math.round(((spreadPercent - this.config.minSpreadPercent) / range) * 100);
  }

  private scoreProfitability(netProfitPercent: number): number {
    if (netProfitPercent <= 0) return 0;
    return Math.min(100, Math.round(netProfitPercent * 200));
  }

  private scoreLatency(latencyMs: number): number {
    if (latencyMs <= this.config.targetLatencyMs) return 100;
    if (latencyMs >= this.config.maxLatencyMs) return 0;
    const range = this.config.maxLatencyMs - this.config.targetLatencyMs;
    return Math.round(((this.config.maxLatencyMs - latencyMs) / range) * 100);
  }

  private scoreFeeCost(feeCostPercent: number): number {
    if (feeCostPercent <= 0) return 100;
    if (feeCostPercent >= 0.5) return 0;
    return Math.round((1 - feeCostPercent / 0.5) * 100);
  }

  private scorePattern(zScore: number): number {
    if (zScore <= 0) return Math.max(0, Math.round(30 + zScore * 10));
    if (zScore >= 3) return 100;
    return Math.round(30 + (zScore / 3) * 70);
  }

  private letterGrade(score: number): ScoredSignal['grade'] {
    if (score >= 85) return 'A';
    if (score >= 70) return 'B';
    if (score >= 55) return 'C';
    if (score >= 40) return 'D';
    return 'F';
  }

  private recommend(score: number): ScoredSignal['recommendation'] {
    if (score >= this.config.executeThreshold) return 'execute';
    if (score >= this.config.waitThreshold) return 'wait';
    return 'skip';
  }

  private buildReason(scores: FactorScores, total: number, grade: string): string {
    const parts: string[] = [];
    if (scores.spread >= 80) parts.push('excellent spread');
    else if (scores.spread >= 50) parts.push('decent spread');
    else parts.push('thin spread');

    if (scores.latency >= 80) parts.push('fast execution');
    else if (scores.latency < 30) parts.push('high latency risk');

    if (scores.liquidity >= 70) parts.push('deep liquidity');
    else if (scores.liquidity < 30) parts.push('shallow liquidity');

    if (scores.pattern >= 80) parts.push('rare pattern (z>2)');
    return `Grade ${grade} (${total}/100): ${parts.join(', ')}`;
  }

  private disqualifiedSignal(factors: SignalFactors): ScoredSignal {
    const reason = !factors.fillable ? 'Orderbook cannot fill requested amount' : 'Exchange(s) not healthy';
    return {
      factors,
      scores: { spread: 0, profitability: 0, liquidity: 0, latency: 0, feeCost: 0, pattern: 0 },
      totalScore: 0, grade: 'F', recommendation: 'skip', reason,
    };
  }

  getHistory(): ScoredSignal[] { return [...this.scoringHistory]; }

  getAverageScore(): number {
    if (this.scoringHistory.length === 0) return 0;
    return this.scoringHistory.reduce((s, sig) => s + sig.totalScore, 0) / this.scoringHistory.length;
  }

  getGradeDistribution(): Record<string, number> {
    const dist: Record<string, number> = { A: 0, B: 0, C: 0, D: 0, F: 0 };
    for (const sig of this.scoringHistory) dist[sig.grade]++;
    return dist;
  }

  getRecommendationDistribution(): Record<string, number> {
    const dist: Record<string, number> = { execute: 0, wait: 0, skip: 0 };
    for (const sig of this.scoringHistory) dist[sig.recommendation]++;
    return dist;
  }

  getConfig(): ScorerConfig {
    return { ...this.config, weights: { ...this.config.weights } };
  }

  clearHistory(): void { this.scoringHistory = []; }
}
