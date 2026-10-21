/**
 * ArbitrageSignalScorer types and default configurations.
 */

export interface SignalFactors {
  spreadPercent: number;           // Gross spread %
  netProfitPercent: number;        // Net profit after fees %
  liquidityScore: number;          // 0-100 from OrderBookAnalyzer
  latencyMs: number;               // Combined buy+sell latency
  feeCostPercent: number;          // Total fees as % of position
  spreadZScore: number;            // From SpreadHistoryTracker (>2 = anomaly)
  fillable: boolean;               // Whether orderbook can fill the amount
  exchangeHealthy: boolean;        // Both exchanges connected and healthy
}

export interface ScoredSignal {
  factors: SignalFactors;
  scores: FactorScores;            // Individual factor scores 0-100
  totalScore: number;              // Weighted total 0-100
  grade: 'A' | 'B' | 'C' | 'D' | 'F';  // Letter grade
  recommendation: 'execute' | 'wait' | 'skip';
  reason: string;
}

export interface FactorScores {
  spread: number;        // 0-100
  profitability: number; // 0-100
  liquidity: number;     // 0-100
  latency: number;       // 0-100
  feeCost: number;       // 0-100
  pattern: number;       // 0-100
}

export interface ScorerWeights {
  spread: number;        // Weight for spread quality (default: 0.25)
  profitability: number; // Weight for net profit (default: 0.25)
  liquidity: number;     // Weight for liquidity depth (default: 0.20)
  latency: number;       // Weight for latency (default: 0.10)
  feeCost: number;       // Weight for fee impact (default: 0.10)
  pattern: number;       // Weight for historical pattern (default: 0.10)
}

export interface ScorerConfig {
  weights: ScorerWeights;
  executeThreshold: number;     // Min score to recommend execution (default: 70)
  waitThreshold: number;        // Min score to recommend waiting (default: 40)
  targetLatencyMs: number;      // Target latency for max score (default: 100)
  maxLatencyMs: number;         // Max acceptable latency (default: 500)
  minSpreadPercent: number;     // Min spread for any score (default: 0.05)
  maxSpreadPercent: number;     // Spread for max score (default: 1.0)
}

export const DEFAULT_SCORER_WEIGHTS: ScorerWeights = {
  spread: 0.25,
  profitability: 0.25,
  liquidity: 0.20,
  latency: 0.10,
  feeCost: 0.10,
  pattern: 0.10,
};

export const DEFAULT_SCORER_CONFIG: ScorerConfig = {
  weights: DEFAULT_SCORER_WEIGHTS,
  executeThreshold: 70,
  waitThreshold: 40,
  targetLatencyMs: 100,
  maxLatencyMs: 500,
  minSpreadPercent: 0.05,
  maxSpreadPercent: 1.0,
};
