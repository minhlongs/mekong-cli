/**
 * AdaptiveSpreadThreshold types and default configurations.
 */

export type VolatilityRegime = 'low' | 'medium' | 'high';

export interface RegimeConfig {
  regime: VolatilityRegime;
  spreadMultiplier: number;    // Multiply base threshold by this factor
  minThreshold: number;        // Absolute minimum threshold for this regime
  maxThreshold: number;        // Absolute maximum threshold for this regime
}

export interface ThresholdState {
  currentThreshold: number;       // Active threshold (basis points)
  baseThreshold: number;          // Base/default threshold
  regime: VolatilityRegime;       // Current volatility regime
  spreadEma: number;              // EMA of recent spreads
  volatilityEma: number;          // EMA of spread volatility
  samplesUsed: number;            // Number of samples in calculation
  lastUpdate: number;
  regimeChanges: number;          // Total regime transitions
}

export interface AdaptiveThresholdConfig {
  baseThresholdBps: number;           // Base threshold in basis points (default: 10 = 0.1%)
  emaAlpha: number;                   // EMA smoothing factor (default: 0.1)
  volatilityAlpha: number;            // Volatility EMA smoothing (default: 0.05)
  regimeConfigs: RegimeConfig[];      // Per-regime multipliers
  regimeLowVolThreshold: number;      // Below this = low vol regime (default: 0.05%)
  regimeHighVolThreshold: number;     // Above this = high vol regime (default: 0.3%)
  minSamplesForAdaptation: number;    // Min samples before adapting (default: 20)
  updateIntervalMs: number;           // How often to recalculate (default: 5000)
  cooldownAfterRegimeChangeMs: number; // Wait after regime change (default: 10000)
}

export const DEFAULT_REGIME_CONFIGS: RegimeConfig[] = [
  { regime: 'low', spreadMultiplier: 1.5, minThreshold: 15, maxThreshold: 50 },
  { regime: 'medium', spreadMultiplier: 1.0, minThreshold: 10, maxThreshold: 30 },
  { regime: 'high', spreadMultiplier: 0.7, minThreshold: 5, maxThreshold: 25 },
];

export const DEFAULT_ADAPTIVE_THRESHOLD_CONFIG: AdaptiveThresholdConfig = {
  baseThresholdBps: 10,
  emaAlpha: 0.1,
  volatilityAlpha: 0.05,
  regimeConfigs: DEFAULT_REGIME_CONFIGS,
  regimeLowVolThreshold: 0.05,
  regimeHighVolThreshold: 0.3,
  minSamplesForAdaptation: 20,
  updateIntervalMs: 5000,
  cooldownAfterRegimeChangeMs: 10000,
};
