/**
 * MultiExchangeConnector types and default configuration.
 */

import { IExchange } from '@mekong/trading-core/interfaces';
import { ExchangeConfig } from './arbitrage-types';

export interface ExchangeHealth {
  exchange: string;
  connected: boolean;
  lastPingMs: number;
  lastPingTime: number;
  failCount: number;
  avgLatencyMs: number;
}

export interface ConnectorConfig {
  healthCheckIntervalMs: number;
  maxFailsBeforeDisable: number;
  autoReconnect: boolean;
  reconnectDelayMs: number;
}

export const DEFAULT_CONNECTOR_CONFIG: ConnectorConfig = {
  healthCheckIntervalMs: 30000,
  maxFailsBeforeDisable: 5,
  autoReconnect: true,
  reconnectDelayMs: 5000,
};

export const SUPPORTED_EXCHANGES = ['binance', 'okx', 'bybit', 'gateio'] as const;
export type SupportedExchange = typeof SUPPORTED_EXCHANGES[number];

/**
 * Factory function type: creates an IExchange from ExchangeConfig.
 * App must provide this to bridge SDK ↔ concrete exchange client.
 */
export type ExchangeFactory = (config: ExchangeConfig) => IExchange;
