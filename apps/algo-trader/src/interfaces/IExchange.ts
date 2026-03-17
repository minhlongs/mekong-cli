/**
 * Exchange interfaces — local definitions replacing @agencyos/trading-core/interfaces.
 */

export interface IOrder {
  id: string;
  symbol: string;
  type?: string;
  side: string;
  amount: number;
  price?: number;
  filled?: number;
  status: string;
  timestamp: number;
  [key: string]: unknown;
}

export interface IBalance {
  [key: string]: {
    free: number;
    used: number;
    total: number;
  } | string | number;
}

export interface IOrderBookEntry {
  price: number;
  amount: number;
}

export interface IOrderBook {
  symbol: string;
  bids: [number, number][];
  asks: [number, number][];
  timestamp: number;
}

export interface IExchange {
  name: string;
  fetchTicker(symbol: string): Promise<Record<string, unknown>>;
  fetchOrderBook(symbol: string): Promise<Record<string, unknown>>;
  createOrder(symbol: string, type: string, side: string, amount: number, price?: number): Promise<Record<string, unknown>>;
  createMarketOrder(symbol: string, side: string, amount: number): Promise<Record<string, unknown>>;
  fetchBalance(): Promise<Record<string, unknown>>;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  [key: string]: unknown;
}

export interface ISignal {
  type: SignalType;
  symbol?: string;
  action?: 'buy' | 'sell' | 'hold';
  strength?: number;
  timestamp: number;
  price?: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ICandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export enum SignalType {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold',
}
