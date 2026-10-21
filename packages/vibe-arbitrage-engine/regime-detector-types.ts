/**
 * RegimeDetector types, default configuration, and math helpers.
 */

export type MarketRegime = 'trending' | 'mean-reverting' | 'volatile' | 'quiet';

export interface RegimeSignal {
  regime: MarketRegime;
  confidence: number;       // 0-1
  hurstExponent: number;    // <0.5 = mean-revert, >0.5 = trending
  volatilityRatio: number;  // short/long vol ratio
  spreadCv: number;         // coefficient of variation
  timestamp: number;
}

export interface RegimeDetectorConfig {
  shortWindow: number;      // Short vol window (default: 20)
  longWindow: number;       // Long vol window (default: 100)
  hurstLag: number;         // R/S lag count (default: 10)
  trendingHurst: number;    // Hurst > this = trending (default: 0.6)
  meanRevertHurst: number;  // Hurst < this = mean-reverting (default: 0.4)
  volatileThreshold: number; // Vol ratio > this = volatile (default: 1.5)
  quietThreshold: number;   // Vol ratio < this = quiet (default: 0.5)
}

export const DEFAULT_REGIME_DETECTOR_CONFIG: RegimeDetectorConfig = {
  shortWindow: 20,
  longWindow: 100,
  hurstLag: 10,
  trendingHurst: 0.6,
  meanRevertHurst: 0.4,
  volatileThreshold: 1.5,
  quietThreshold: 0.5,
};

export function calcMean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

export function calcStddev(arr: number[]): number {
  if (arr.length < 2) return 0;
  const m = calcMean(arr);
  const variance = arr.reduce((s, v) => s + (v - m) ** 2, 0) / (arr.length - 1);
  return Math.sqrt(variance);
}

export function calcLinearRegressionSlope(x: number[], y: number[]): number {
  const n = x.length;
  const mx = calcMean(x);
  const my = calcMean(y);
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {
    num += (x[i] - mx) * (y[i] - my);
    den += (x[i] - mx) ** 2;
  }
  return den === 0 ? 0.5 : num / den;
}

export function calcRescaledRange(data: number[]): number {
  if (data.length < 2) return 0;
  const mean = calcMean(data);
  const deviations = data.map(d => d - mean);
  const cumDev: number[] = [];
  let sum = 0;
  for (const d of deviations) {
    sum += d;
    cumDev.push(sum);
  }
  const range = Math.max(...cumDev) - Math.min(...cumDev);
  const s = calcStddev(data);
  return s === 0 ? 0 : range / s;
}
