/**
 * AdaptiveSpreadThreshold — Dynamic spread threshold based on market volatility.
 */

import { getArbLogger } from './arb-logger';
import {
  VolatilityRegime, ThresholdState, AdaptiveThresholdConfig,
  DEFAULT_REGIME_CONFIGS, DEFAULT_ADAPTIVE_THRESHOLD_CONFIG,
} from './adaptive-spread-types';

export * from './adaptive-spread-types';

const logger = getArbLogger();

export class AdaptiveSpreadThreshold {
  private config: AdaptiveThresholdConfig;
  private spreadHistory: number[] = [];
  private currentThreshold: number;
  private spreadEma = 0;
  private volatilityEma = 0;
  private currentRegime: VolatilityRegime = 'medium';
  private sampleCount = 0;
  private lastRegimeChangeTime = 0;
  private regimeChangeCount = 0;
  private updateTimer: NodeJS.Timeout | null = null;

  constructor(config?: Partial<AdaptiveThresholdConfig>) {
    this.config = { ...DEFAULT_ADAPTIVE_THRESHOLD_CONFIG, ...config };
    if (!this.config.regimeConfigs || this.config.regimeConfigs.length === 0) {
      this.config.regimeConfigs = DEFAULT_REGIME_CONFIGS;
    }
    this.currentThreshold = this.config.baseThresholdBps;
  }

  observeSpread(spreadPercent: number): void {
    this.sampleCount++;
    this.spreadHistory.push(spreadPercent);
    if (this.spreadHistory.length > 500) {
      this.spreadHistory.splice(0, this.spreadHistory.length - 500);
    }

    if (this.sampleCount === 1) {
      this.spreadEma = spreadPercent;
      this.volatilityEma = 0;
    } else {
      const prevEma = this.spreadEma;
      this.spreadEma = this.config.emaAlpha * spreadPercent + (1 - this.config.emaAlpha) * this.spreadEma;
      const deviation = Math.abs(spreadPercent - prevEma);
      this.volatilityEma = this.config.volatilityAlpha * deviation + (1 - this.config.volatilityAlpha) * this.volatilityEma;
    }

    if (this.sampleCount >= this.config.minSamplesForAdaptation) {
      this.updateRegime();
      this.updateThreshold();
    }
  }

  getThreshold(): number { return this.currentThreshold; }
  getThresholdPercent(): number { return this.currentThreshold / 100; }
  meetsThreshold(spreadPercent: number): boolean { return spreadPercent >= this.getThresholdPercent(); }

  getState(): ThresholdState {
    return {
      currentThreshold: this.currentThreshold,
      baseThreshold: this.config.baseThresholdBps,
      regime: this.currentRegime,
      spreadEma: this.spreadEma,
      volatilityEma: this.volatilityEma,
      samplesUsed: this.sampleCount,
      lastUpdate: Date.now(),
      regimeChanges: this.regimeChangeCount,
    };
  }

  getRegime(): VolatilityRegime { return this.currentRegime; }

  isInCooldown(): boolean {
    return (Date.now() - this.lastRegimeChangeTime) < this.config.cooldownAfterRegimeChangeMs;
  }

  startAutoUpdate(): void {
    if (this.updateTimer) return;
    this.updateTimer = setInterval(() => {
      if (this.sampleCount >= this.config.minSamplesForAdaptation) {
        this.updateRegime();
        this.updateThreshold();
      }
    }, this.config.updateIntervalMs);
  }

  stopAutoUpdate(): void {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  reset(): void {
    this.spreadHistory = [];
    this.currentThreshold = this.config.baseThresholdBps;
    this.spreadEma = 0;
    this.volatilityEma = 0;
    this.currentRegime = 'medium';
    this.sampleCount = 0;
    this.lastRegimeChangeTime = 0;
    this.regimeChangeCount = 0;
    this.stopAutoUpdate();
  }

  private updateRegime(): void {
    let newRegime: VolatilityRegime;
    if (this.volatilityEma < this.config.regimeLowVolThreshold) newRegime = 'low';
    else if (this.volatilityEma > this.config.regimeHighVolThreshold) newRegime = 'high';
    else newRegime = 'medium';

    if (newRegime !== this.currentRegime) {
      const oldRegime = this.currentRegime;
      this.currentRegime = newRegime;
      this.lastRegimeChangeTime = Date.now();
      this.regimeChangeCount++;
      logger.info(
        `[AdaptiveThreshold] Regime change: ${oldRegime} → ${newRegime} ` +
        `(vol EMA: ${this.volatilityEma.toFixed(4)}%, changes: ${this.regimeChangeCount})`
      );
    }
  }

  private updateThreshold(): void {
    const regimeConfig = this.config.regimeConfigs.find(r => r.regime === this.currentRegime);
    if (!regimeConfig) return;

    let newThreshold = this.config.baseThresholdBps * regimeConfig.spreadMultiplier;
    if (this.spreadEma > 0) {
      const spreadBps = this.spreadEma * 100;
      if (spreadBps > newThreshold * 2) newThreshold *= 0.9;
    }

    newThreshold = Math.max(regimeConfig.minThreshold, Math.min(regimeConfig.maxThreshold, newThreshold));
    this.currentThreshold = Math.round(newThreshold * 100) / 100;
  }
}
