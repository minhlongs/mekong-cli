/**
 * AgiArbitrageEngine — Intelligent multi-exchange spread detector + execution engine.
 */

import { getArbLogger } from './arb-logger';
import { SpreadDetectorEngine, DetectionEvent } from './spread-detector-engine';
import { RegimeDetector, MarketRegime, RegimeSignal } from './regime-detector';
import { KellyPositionSizer, KellyResult } from './kelly-position-sizer';
import {
  AgiConfig, AgiStats, DEFAULT_REGIME_PARAMS, DEFAULT_AGI_CONFIG,
} from './agi-arbitrage-types';

export * from './agi-arbitrage-types';

export class AgiArbitrageEngine {
  private config: AgiConfig;
  private engine: SpreadDetectorEngine;
  private regimeDetector = new RegimeDetector();
  private kellySizer: KellyPositionSizer;

  private isRunning = false;
  private regimeTimer: ReturnType<typeof setInterval> | null = null;
  private currentRegime: MarketRegime = 'quiet';
  private regimeConfidence = 0;
  private emaProfitability = 0;
  private baseScoreThreshold: number;
  private baseSpreadThreshold: number;
  private totalRegimeShifts = 0;
  private lastTradeCount = 0;
  private currentEquity: number;

  constructor(config?: Partial<AgiConfig>) {
    this.config = {
      ...DEFAULT_AGI_CONFIG, ...config,
      regimeParams: { ...DEFAULT_REGIME_PARAMS, ...config?.regimeParams },
    };
    this.currentEquity = this.config.initialEquity;
    this.baseScoreThreshold = this.config.engine.scorer?.executeThreshold ?? 65;
    this.baseSpreadThreshold = this.config.engine.scanner?.minSpreadPercent ?? 0.05;
    this.engine = new SpreadDetectorEngine(this.config.engine);
    this.kellySizer = new KellyPositionSizer({
      maxPositionUsd: this.config.engine.executor?.maxPositionSizeUsd ?? 5000,
    });
  }

  async init(): Promise<string[]> {
    const log = getArbLogger();
    log.info('[AGI] Initializing AgiArbitrageEngine...');
    const connected = await this.engine.init();
    log.info(`[AGI] Connected: ${connected.join(', ')} | Regime: ${this.config.enableRegimeDetection ? 'ON' : 'OFF'} | Kelly: ${this.config.enableKellySizing ? 'ON' : 'OFF'} | Self-tune: ${this.config.enableSelfTuning ? 'ON' : 'OFF'}`);
    return connected;
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    const log = getArbLogger();
    log.info('[AGI] Starting AGI arbitrage engine...');
    await this.engine.start();
    if (this.config.enableRegimeDetection) {
      this.regimeTimer = setInterval(() => this.regimeTick(), this.config.regimeIntervalMs);
    }
    log.info('[AGI] AGI engine ACTIVE — intelligent spread detection running');
  }

  stop(): void {
    this.isRunning = false;
    if (this.regimeTimer) { clearInterval(this.regimeTimer); this.regimeTimer = null; }
    this.engine.stop();
    getArbLogger().info('[AGI] Engine STOPPED');
  }

  private regimeTick(): void {
    if (!this.isRunning) return;
    for (const ev of this.engine.getEvents(20)) {
      this.regimeDetector.addSpread(ev.opportunity.spreadPercent);
    }
    const signal = this.regimeDetector.detect();
    const prevRegime = this.currentRegime;
    this.currentRegime = signal.regime;
    this.regimeConfidence = signal.confidence;

    if (prevRegime !== this.currentRegime) {
      this.totalRegimeShifts++;
      getArbLogger().info(`[AGI] Regime shift: ${prevRegime} → ${this.currentRegime} (confidence: ${(signal.confidence * 100).toFixed(0)}%, hurst: ${signal.hurstExponent.toFixed(2)})`);
    }
    if (this.config.enableSelfTuning) this.selfTune();
    if (this.config.enableKellySizing) this.updateKelly();
  }

  private selfTune(): void {
    const profit = this.engine.getProfitSummary();
    const currentTradeCount = this.engine.getStats().totalExecuted;
    if (currentTradeCount > this.lastTradeCount) {
      for (const ev of this.engine.getEvents(currentTradeCount - this.lastTradeCount)) {
        if (ev.executed && ev.result) this.kellySizer.recordTrade(ev.result.actualProfitUsd);
      }
      this.lastTradeCount = currentTradeCount;
    }
    const currentPnl = profit.cumulativePnl;
    this.emaProfitability = this.config.tuningAlpha * currentPnl + (1 - this.config.tuningAlpha) * this.emaProfitability;
    this.currentEquity = this.config.initialEquity + currentPnl;
  }

  private updateKelly(): void {
    const kelly = this.kellySizer.calculate(this.currentEquity, this.currentRegime);
    if (kelly.tradesAnalyzed >= 10) {
      getArbLogger().info(
        `[AGI] Kelly: f*=${(kelly.kellyFraction * 100).toFixed(1)}% | adj=${(kelly.adjustedFraction * 100).toFixed(1)}% | size=$${kelly.positionSizeUsd.toFixed(0)} | WR=${(kelly.winRate * 100).toFixed(0)}% | edge=${kelly.edgePercent.toFixed(1)}%`
      );
    }
  }

  getEffectiveScoreThreshold(): number {
    const params = this.config.regimeParams[this.currentRegime];
    const adjusted = this.baseScoreThreshold + params.scoreThresholdAdjust;
    const tuningAdjust = this.config.enableSelfTuning ? (this.emaProfitability > 0 ? -3 : 3) : 0;
    return Math.max(this.config.minScoreThreshold, Math.min(this.config.maxScoreThreshold, adjusted + tuningAdjust));
  }

  getEffectiveSpreadThreshold(): number {
    return this.baseSpreadThreshold * this.config.regimeParams[this.currentRegime].spreadThresholdMultiplier;
  }

  getKellyResult(): KellyResult { return this.kellySizer.calculate(this.currentEquity, this.currentRegime); }
  getRegimeSignal(): RegimeSignal { return this.regimeDetector.detect(); }

  getStats(): AgiStats {
    const baseStats = this.engine.getStats();
    const regimeDist = this.regimeDetector.getRegimeDistribution();
    const kelly = this.kellySizer.calculate(this.currentEquity, this.currentRegime);

    return {
      ...baseStats,
      currentRegime: this.currentRegime,
      regimeConfidence: this.regimeConfidence,
      kellyFraction: kelly.adjustedFraction,
      currentPositionSize: kelly.positionSizeUsd,
      effectiveScoreThreshold: this.getEffectiveScoreThreshold(),
      effectiveSpreadThreshold: this.getEffectiveSpreadThreshold(),
      emaProfitability: this.emaProfitability,
      regimeHistory: Object.entries(regimeDist).map(([regime, count]) => ({
        regime: regime as MarketRegime, count,
      })),
      totalRegimeShifts: this.totalRegimeShifts,
    };
  }

  getEngine(): SpreadDetectorEngine { return this.engine; }
  getProfitSummary() { return this.engine.getProfitSummary(); }
  getEvents(limit?: number): DetectionEvent[] { return this.engine.getEvents(limit); }

  emergencyStop(reason: string): void {
    this.engine.emergencyStop(reason);
    this.stop();
    getArbLogger().warn(`[AGI] EMERGENCY STOP: ${reason}`);
  }

  isActive(): boolean { return this.isRunning; }
}
