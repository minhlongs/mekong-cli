/**
 * BalanceRebalancer types and default configurations.
 */

export interface ExchangeBalance {
  exchange: string;
  currency: string;
  available: number;
  total: number;
  valueUsd: number;     // Available * current price
}

export interface BalanceSnapshot {
  timestamp: number;
  balances: ExchangeBalance[];
  totalValueUsd: number;
}

export interface TransferSuggestion {
  fromExchange: string;
  toExchange: string;
  currency: string;
  amount: number;
  valueUsd: number;
  reason: string;
  priority: 'low' | 'medium' | 'high';
}

export interface TransferRecord {
  id: number;
  timestamp: number;
  fromExchange: string;
  toExchange: string;
  currency: string;
  amount: number;
  valueUsd: number;
  status: 'pending' | 'completed' | 'failed';
}

export interface ImbalanceReport {
  currency: string;
  exchanges: { exchange: string; available: number; valueUsd: number; sharePercent: number }[];
  maxSharePercent: number;
  minSharePercent: number;
  imbalancePercent: number;   // max - min share
  isImbalanced: boolean;
}

export interface RebalancerConfig {
  imbalanceThresholdPercent: number;  // Trigger rebalance when imbalance > this (default: 30)
  minTransferUsd: number;             // Min transfer value to suggest (default: 50)
  targetSharePercent: number;         // Target equal share per exchange (auto-calc if 0)
  maxHistorySize: number;             // Max balance snapshots to keep (default: 500)
}

export const DEFAULT_REBALANCER_CONFIG: RebalancerConfig = {
  imbalanceThresholdPercent: 30,
  minTransferUsd: 50,
  targetSharePercent: 0,  // Auto-calc: 100 / numExchanges
  maxHistorySize: 500,
};
