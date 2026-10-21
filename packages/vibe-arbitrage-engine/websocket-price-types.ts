/**
 * WebSocketPriceFeed types, endpoints, and default configuration.
 */

export interface WsPriceUpdate {
  exchange: string;
  symbol: string;
  bid: number;
  ask: number;
  mid: number;
  timestamp: number;
  latencyMs: number;
}

export interface WsConnectionState {
  exchange: string;
  connected: boolean;
  subscribedSymbols: string[];
  lastMessageTime: number;
  reconnectCount: number;
  messagesReceived: number;
  avgLatencyMs: number;
}

export interface WsFeedConfig {
  heartbeatIntervalMs: number;
  staleThresholdMs: number;
  reconnectDelayMs: number;
  maxReconnectDelayMs: number;
  maxReconnectAttempts: number;
  bufferSize: number;
}

export const DEFAULT_WS_FEED_CONFIG: WsFeedConfig = {
  heartbeatIntervalMs: 15000,
  staleThresholdMs: 30000,
  reconnectDelayMs: 1000,
  maxReconnectDelayMs: 30000,
  maxReconnectAttempts: 10,
  bufferSize: 50,
};

export const WS_ENDPOINTS: Record<string, string> = {
  binance: 'wss://stream.binance.com:9443/ws',
  okx: 'wss://ws.okx.com:8443/ws/v5/public',
  bybit: 'wss://stream.bybit.com/v5/public/spot',
  gateio: 'wss://api.gateio.ws/ws/v4/',
};
