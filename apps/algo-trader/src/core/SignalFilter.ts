/**
 * SignalFilter — Pre-trade signal quality filter.
 * Market regime detection, signal scoring, cooldown, volume confirmation.
 * Sits between SignalGenerator and order execution.
 */

import { ICandle } from '../interfaces/ICandle';
import { SignalType } from '../interfaces/IStrategy';
import { ConsensusSignal } from './SignalGenerator';

export type MarketRegime = 'trending' | 'ranging' | 'volatile';

export interface RegimeState {
  regime: MarketRegime;
  adx: number;          // Average Directional Index (0-100)
  volatilityRatio: number; // Current vs historical volatility
  trendStrength: number;   // 0-1 confidence in trend
}

export interface SignalScore {
  total: number;          // 0-100 composite score
  regimeAlignment: number; // How well signal fits current regime
  volumeScore: number;     // Volume confirmation strength
  momentumScore: number;   // Momentum alignment
  confluenceScore: number; // Multi-factor confluence
}

export interface FilterResult {
  pass: boolean;
  signal: ConsensusSignal;
  score: SignalScore;
  regime: RegimeState;
  rejectReason?: string;
}

export interface SignalFilterConfig {
  minScore: number;              // Minimum score to pass (default: 50)
  cooldownMs: number;            // Min ms between trades (default: 3600000 = 1h)
  minVolume: number;             // Min volume ratio vs avg (default: 0.5)
  adxTrendThreshold: number;     // ADX > this = trending (default: 25)
  adxRangingThreshold: number;   // ADX < this = ranging (default: 20)
  volatilityHighThreshold: number; // Vol ratio > this = volatile (default: 2.0)
  lookbackPeriod: number;        // Candles for regime calculation (default: 50)
}

const DEFAULT_CONFIG: SignalFilterConfig = {
  minScore: 50,
  cooldownMs: 3600000,
  minVolume: 0.5,
  adxTrendThreshold: 25,
  adxRangingThreshold: 20,
  volatilityHighThreshold: 2.0,
  lookbackPeriod: 50,
};

export class SignalFilter {
  private config: SignalFilterConfig;
  private recentCandles: ICandle[] = [];
  private lastTradeTime = 0;

  constructor(config?: Partial<SignalFilterConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Feed candle data for regime detection.
   * Must be called before evaluate() for accurate regime detection.
   */
  updateCandle(candle: ICandle): void {
    this.recentCandles.push(candle);
    // Keep only lookback + buffer
    const maxLen = this.config.lookbackPeriod + 20;
    if (this.recentCandles.length > maxLen) {
      this.recentCandles = this.recentCandles.slice(-maxLen);
    }
  }

  /**
   * Evaluate a consensus signal through all filters.
   */
  evaluate(signal: ConsensusSignal, currentCandle: ICandle): FilterResult {
    const regime = this.detectRegime();
    const score = this.scoreSignal(signal, currentCandle, regime);

    // Cooldown check
    if (this.lastTradeTime > 0 && (currentCandle.timestamp - this.lastTradeTime) < this.config.cooldownMs) {
      return { pass: false, signal, score, regime, rejectReason: 'cooldown_active' };
    }

    // Volume check
    if (score.volumeScore < this.config.minVolume * 100) {
      return { pass: false, signal, score, regime, rejectReason: 'low_volume' };
    }

    // Score threshold
    if (score.total < this.config.minScore) {
      return { pass: false, signal, score, regime, rejectReason: `score_${score.total}_below_${this.config.minScore}` };
    }

    return { pass: true, signal, score, regime };
  }

  /**
   * Mark that a trade was executed (for cooldown tracking).
   */
  recordTrade(timestamp: number): void {
    this.lastTradeTime = timestamp;
  }

  /**
   * Detect current market regime from recent candles.
   */
  detectRegime(): RegimeState {
    if (this.recentCandles.length < 14) {
      return { regime: 'ranging', adx: 0, volatilityRatio: 1, trendStrength: 0 };
    }

    const closes = this.recentCandles.map(c => c.close);
    const period = Math.min(this.config.lookbackPeriod, closes.length);
    const recent = closes.slice(-period);

    // Simplified ADX calculation using directional movement
    const adx = this.calculateADX(this.recentCandles.slice(-period));

    // Volatility ratio: recent stddev vs longer-term stddev
    const recentVol = this.stddev(recent.slice(-14));
    const historicalVol = this.stddev(recent);
    const volatilityRatio = historicalVol > 0 ? recentVol / historicalVol : 1;

    // Trend strength: linear regression R-squared
    const trendStrength = this.rSquared(recent);

    let regime: MarketRegime;
    if (volatilityRatio > this.config.volatilityHighThreshold) {
      regime = 'volatile';
    } else if (adx > this.config.adxTrendThreshold) {
      regime = 'trending';
    } else {
      regime = 'ranging';
    }

    return { regime, adx, volatilityRatio, trendStrength };
  }

  /**
   * Score a signal on 0-100 scale based on multiple factors.
   */
  private scoreSignal(signal: ConsensusSignal, candle: ICandle, regime: RegimeState): SignalScore {
    // 1. Regime alignment (0-25): trend signals work best in trending, etc.
    let regimeAlignment = 15; // neutral
    if (regime.regime === 'trending' && signal.confidence > 0.7) {
      regimeAlignment = 25; // high confidence + trending = great
    } else if (regime.regime === 'volatile') {
      regimeAlignment = 5; // volatile = risky for any signal
    } else if (regime.regime === 'ranging' && signal.confidence < 0.5) {
      regimeAlignment = 8; // weak signal in range = bad
    }

    // 2. Volume score (0-25): compare current volume to average
    const avgVolume = this.averageVolume();
    const volumeScore = avgVolume > 0
      ? Math.min(25, (candle.volume / avgVolume) * 15)
      : 12.5;

    // 3. Momentum score (0-25): price direction alignment with signal
    const momentumScore = this.calculateMomentumScore(signal.type);

    // 4. Confluence score (0-25): based on consensus confidence + vote count
    const voteRatio = signal.votes.length / Math.max(signal.metadata.totalWeight, 1);
    const confluenceScore = Math.min(25, signal.confidence * 20 + voteRatio * 5);

    const total = Math.round(regimeAlignment + volumeScore + momentumScore + confluenceScore);

    return {
      total: Math.min(100, Math.max(0, total)),
      regimeAlignment,
      volumeScore,
      momentumScore,
      confluenceScore,
    };
  }

  /** Simplified ADX: average absolute price change direction consistency */
  private calculateADX(candles: ICandle[]): number {
    if (candles.length < 14) return 0;

    let plusDM = 0;
    let minusDM = 0;
    let trSum = 0;

    for (let i = 1; i < candles.length; i++) {
      const high = candles[i].high;
      const low = candles[i].low;
      const prevHigh = candles[i - 1].high;
      const prevLow = candles[i - 1].low;
      const prevClose = candles[i - 1].close;

      const upMove = high - prevHigh;
      const downMove = prevLow - low;

      if (upMove > downMove && upMove > 0) plusDM += upMove;
      if (downMove > upMove && downMove > 0) minusDM += downMove;

      const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
      trSum += tr;
    }

    if (trSum === 0) return 0;

    const plusDI = (plusDM / trSum) * 100;
    const minusDI = (minusDM / trSum) * 100;
    const diSum = plusDI + minusDI;

    if (diSum === 0) return 0;
    return (Math.abs(plusDI - minusDI) / diSum) * 100;
  }

  /** Calculate momentum alignment score (0-25) */
  private calculateMomentumScore(signalType: SignalType): number {
    if (this.recentCandles.length < 10) return 12.5;

    const recent = this.recentCandles.slice(-10);
    const firstClose = recent[0].close;
    const lastClose = recent[recent.length - 1].close;
    const pctChange = ((lastClose - firstClose) / firstClose) * 100;

    // BUY signal + positive momentum = aligned
    if (signalType === SignalType.BUY && pctChange > 0) {
      return Math.min(25, 15 + pctChange * 2);
    }
    // SELL signal + negative momentum = aligned
    if (signalType === SignalType.SELL && pctChange < 0) {
      return Math.min(25, 15 + Math.abs(pctChange) * 2);
    }
    // Counter-trend: lower score but not zero (mean reversion possible)
    return Math.max(5, 12 - Math.abs(pctChange));
  }

  /** Average volume over recent candles */
  private averageVolume(): number {
    if (this.recentCandles.length === 0) return 0;
    return this.recentCandles.reduce((s, c) => s + c.volume, 0) / this.recentCandles.length;
  }

  /** Standard deviation of number array */
  private stddev(values: number[]): number {
    if (values.length < 2) return 0;
    const mean = values.reduce((s, v) => s + v, 0) / values.length;
    const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / (values.length - 1);
    return Math.sqrt(variance);
  }

  /** R-squared of linear regression — measures trend strength (0-1) */
  private rSquared(values: number[]): number {
    if (values.length < 3) return 0;

    const n = values.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += values[i];
      sumXY += i * values[i];
      sumX2 += i * i;
      sumY2 += values[i] * values[i];
    }

    const num = n * sumXY - sumX * sumY;
    const den = Math.sqrt((n * sumX2 - sumX ** 2) * (n * sumY2 - sumY ** 2));

    if (den === 0) return 0;
    const r = num / den;
    return r * r; // R-squared
  }
}
