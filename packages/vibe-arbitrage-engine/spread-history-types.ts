/**
 * SpreadHistoryTracker types and default configuration.
 */

export interface SpreadRecord {
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  spreadPercent: number;
  timestamp: number;
}

export interface SpreadStats {
  pairKey: string;           // "binance→okx:BTC/USDT"
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  mean: number;              // Mean spread %
  stddev: number;            // Standard deviation
  min: number;
  max: number;
  median: number;
  count: number;
  lastSpread: number;
  lastTimestamp: number;
}

export interface SpreadZScore {
  pairKey: string;
  currentSpread: number;
  mean: number;
  stddev: number;
  zScore: number;            // How many stddev above mean (>2 = unusual opportunity)
  isAnomaly: boolean;        // zScore > anomalyThreshold
}

export interface HourlyPattern {
  hour: number;              // 0-23 UTC
  avgSpread: number;
  tradeCount: number;
  bestSpread: number;
}

export interface SpreadHistoryConfig {
  maxRecordsPerPair: number;     // Max records to keep per pair (default: 1000)
  anomalyThreshold: number;      // Z-score threshold for anomaly (default: 2.0)
  patternWindowHours: number;    // Hours to analyze for hourly pattern (default: 168 = 7 days)
}

export const DEFAULT_SPREAD_HISTORY_CONFIG: SpreadHistoryConfig = {
  maxRecordsPerPair: 1000,
  anomalyThreshold: 2.0,
  patternWindowHours: 168,
};
