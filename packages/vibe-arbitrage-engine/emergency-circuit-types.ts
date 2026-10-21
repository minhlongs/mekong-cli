/**
 * EmergencyCircuitBreaker types and default configuration.
 */

export type CircuitState = 'closed' | 'open' | 'half_open';

export interface TripEvent {
  timestamp: number;
  reason: string;
  trigger: 'daily_loss' | 'loss_streak' | 'rapid_loss' | 'manual' | 'exchange_anomaly';
  details: Record<string, number | string>;
}

export interface CircuitBreakerConfig {
  maxDailyLossUsd: number;          // Trip when daily loss exceeds (default: 100)
  maxConsecutiveLosses: number;     // Trip after N consecutive losses (default: 5)
  rapidLossWindowMs: number;        // Window for rapid loss detection (default: 60000 = 1min)
  rapidLossCount: number;           // Trip if N losses in rapid window (default: 3)
  cooldownMs: number;               // Auto-reset after this (default: 300000 = 5min)
  halfOpenMaxTrades: number;        // Trades allowed in half-open before closing (default: 2)
}

export const DEFAULT_CIRCUIT_BREAKER_CONFIG: CircuitBreakerConfig = {
  maxDailyLossUsd: 100,
  maxConsecutiveLosses: 5,
  rapidLossWindowMs: 60000,
  rapidLossCount: 3,
  cooldownMs: 300000,
  halfOpenMaxTrades: 2,
};
