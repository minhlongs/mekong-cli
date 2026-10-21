/**
 * RegimeDetector — Market regime classification for adaptive strategy routing.
 */

import {
  MarketRegime, RegimeSignal, RegimeDetectorConfig, DEFAULT_REGIME_DETECTOR_CONFIG,
  calcMean, calcStddev, calcLinearRegressionSlope, calcRescaledRange,
} from './regime-detector-types';

export * from './regime-detector-types';

export class RegimeDetector {
  private config: RegimeDetectorConfig;
  private spreads: number[] = [];
  private history: RegimeSignal[] = [];

  constructor(config?: Partial<RegimeDetectorConfig>) {
    this.config = { ...DEFAULT_REGIME_DETECTOR_CONFIG, ...config };
  }

  addSpread(spreadPercent: number): void {
    this.spreads.push(spreadPercent);
    const maxLen = this.config.longWindow * 2;
    if (this.spreads.length > maxLen) {
      this.spreads = this.spreads.slice(-maxLen);
    }
  }

  detect(): RegimeSignal {
    const now = Date.now();
    if (this.spreads.length < this.config.shortWindow) {
      const signal: RegimeSignal = {
        regime: 'quiet', confidence: 0, hurstExponent: 0.5,
        volatilityRatio: 1, spreadCv: 0, timestamp: now,
      };
      this.history.push(signal);
      return signal;
    }

    const volatilityRatio = this.calcVolatilityRatio();
    const hurstExponent = this.calcHurstExponent();
    const spreadCv = this.calcCoefficientOfVariation();
    const { regime, confidence } = this.classify(volatilityRatio, hurstExponent, spreadCv);

    const signal: RegimeSignal = {
      regime, confidence, hurstExponent, volatilityRatio, spreadCv, timestamp: now,
    };

    this.history.push(signal);
    if (this.history.length > 500) this.history.splice(0, this.history.length - 500);
    return signal;
  }

  private calcVolatilityRatio(): number {
    const shortVol = calcStddev(this.spreads.slice(-this.config.shortWindow));
    const longVol = calcStddev(
      this.spreads.slice(-Math.min(this.spreads.length, this.config.longWindow))
    );
    return longVol === 0 ? 1 : shortVol / longVol;
  }

  private calcHurstExponent(): number {
    const data = this.spreads.slice(-Math.min(this.spreads.length, this.config.longWindow));
    if (data.length < 10) return 0.5;

    const lags: number[] = [];
    const rsValues: number[] = [];

    for (let lag = 2; lag <= Math.min(this.config.hurstLag, Math.floor(data.length / 2)); lag++) {
      const chunkSize = Math.floor(data.length / lag);
      if (chunkSize < 2) continue;

      let rsSum = 0;
      let chunks = 0;
      for (let i = 0; i < lag; i++) {
        const chunk = data.slice(i * chunkSize, (i + 1) * chunkSize);
        const rs = calcRescaledRange(chunk);
        if (rs > 0) {
          rsSum += rs;
          chunks++;
        }
      }

      if (chunks > 0) {
        lags.push(Math.log(chunkSize));
        rsValues.push(Math.log(rsSum / chunks));
      }
    }

    return lags.length < 2 ? 0.5 : calcLinearRegressionSlope(lags, rsValues);
  }

  private calcCoefficientOfVariation(): number {
    const recent = this.spreads.slice(-this.config.shortWindow);
    const m = calcMean(recent);
    return m === 0 ? 0 : calcStddev(recent) / Math.abs(m);
  }

  private classify(volRatio: number, hurst: number, cv: number): { regime: MarketRegime; confidence: number } {
    if (volRatio > this.config.volatileThreshold) {
      const confidence = Math.min(1, (volRatio - this.config.volatileThreshold) / 1.0);
      return { regime: 'volatile', confidence: 0.5 + confidence * 0.5 };
    }
    if (volRatio < this.config.quietThreshold && cv < 0.3) {
      const confidence = Math.min(1, (this.config.quietThreshold - volRatio) / this.config.quietThreshold);
      return { regime: 'quiet', confidence: 0.5 + confidence * 0.5 };
    }
    if (hurst > this.config.trendingHurst) {
      const confidence = Math.min(1, (hurst - this.config.trendingHurst) / 0.3);
      return { regime: 'trending', confidence: 0.5 + confidence * 0.5 };
    }
    if (hurst < this.config.meanRevertHurst) {
      const confidence = Math.min(1, (this.config.meanRevertHurst - hurst) / 0.3);
      return { regime: 'mean-reverting', confidence: 0.5 + confidence * 0.5 };
    }
    return { regime: 'quiet', confidence: 0.3 };
  }

  getHistory(): RegimeSignal[] { return [...this.history]; }

  getLatestRegime(): MarketRegime {
    return this.history.length > 0 ? this.history[this.history.length - 1].regime : 'quiet';
  }

  getRegimeDistribution(): Record<MarketRegime, number> {
    const dist: Record<MarketRegime, number> = { trending: 0, 'mean-reverting': 0, volatile: 0, quiet: 0 };
    for (const s of this.history) dist[s.regime]++;
    return dist;
  }

  getSpreadCount(): number { return this.spreads.length; }

  reset(): void {
    this.spreads = [];
    this.history = [];
  }
}
