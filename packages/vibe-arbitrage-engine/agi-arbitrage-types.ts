/**
 * AgiArbitrageEngine types and default configurations.
 */

import { SpreadDetectorConfig, EngineStats } from './spread-detector-engine';
import { MarketRegime } from './regime-detector';

export interface AgiConfig {
  /** Base SpreadDetectorEngine config */
  engine: Partial<SpreadDetectorConfig>;
  /** Enable regime detection (default: true) */
  enableRegimeDetection: boolean;
  /** Enable Kelly position sizing (default: true) */
  enableKellySizing: boolean;
  /** Enable self-tuning thresholds (default: true) */
  enableSelfTuning: boolean;
  /** Regime detection interval ms (default: 30000) */
  regimeIntervalMs: number;
  /** EMA alpha for profitability smoothing (default: 0.1) */
  tuningAlpha: number;
  /** Min score threshold floor (default: 40) */
  minScoreThreshold: number;
  /** Max score threshold ceiling (default: 90) */
  maxScoreThreshold: number;
  /** Initial equity USD */
  initialEquity: number;
  /** Regime parameter overrides */
  regimeParams: Record<MarketRegime, RegimeExecutionParams>;
}

export interface RegimeExecutionParams {
  scoreThresholdAdjust: number;      // Added to base score threshold
  spreadThresholdMultiplier: number; // Multiplied with base min spread
  maxConcurrentTrades: number;
  positionSizeMultiplier: number;    // Multiplied with Kelly output
}

export interface AgiStats extends EngineStats {
  currentRegime: MarketRegime;
  regimeConfidence: number;
  kellyFraction: number;
  currentPositionSize: number;
  effectiveScoreThreshold: number;
  effectiveSpreadThreshold: number;
  emaProfitability: number;
  regimeHistory: { regime: MarketRegime; count: number }[];
  totalRegimeShifts: number;
}

export const DEFAULT_REGIME_PARAMS: Record<MarketRegime, RegimeExecutionParams> = {
  'trending': {
    scoreThresholdAdjust: -5,
    spreadThresholdMultiplier: 0.8,
    maxConcurrentTrades: 5,
    positionSizeMultiplier: 1.2,
  },
  'mean-reverting': {
    scoreThresholdAdjust: -10,
    spreadThresholdMultiplier: 0.7,
    maxConcurrentTrades: 5,
    positionSizeMultiplier: 1.0,
  },
  'volatile': {
    scoreThresholdAdjust: 10,
    spreadThresholdMultiplier: 1.5,
    maxConcurrentTrades: 2,
    positionSizeMultiplier: 0.6,
  },
  'quiet': {
    scoreThresholdAdjust: 0,
    spreadThresholdMultiplier: 1.0,
    maxConcurrentTrades: 3,
    positionSizeMultiplier: 0.8,
  },
};

export const DEFAULT_AGI_CONFIG: AgiConfig = {
  engine: {},
  enableRegimeDetection: true,
  enableKellySizing: true,
  enableSelfTuning: true,
  regimeIntervalMs: 30000,
  tuningAlpha: 0.1,
  minScoreThreshold: 40,
  maxScoreThreshold: 90,
  initialEquity: 10000,
  regimeParams: DEFAULT_REGIME_PARAMS,
};
