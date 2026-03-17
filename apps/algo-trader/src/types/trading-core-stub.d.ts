/**
 * Module stubs for @agencyos/trading-core
 * Used for TypeScript compilation when package is not available
 */

declare module '@agencyos/trading-core/exchanges' {
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

  export class ExchangeClientBase {
    constructor(config?: Record<string, unknown>);
    name: string;
    fetchTicker(symbol: string): Promise<Record<string, unknown>>;
    fetchOrderBook(symbol: string): Promise<Record<string, unknown>>;
    createOrder(symbol: string, type: string, side: string, amount: number, price?: number, ...args: unknown[]): Promise<Record<string, unknown>>;
    createMarketOrder(symbol: string, side: string, amount: number): Promise<Record<string, unknown>>;
    fetchBalance(): Promise<Record<string, unknown>>;
    connect(): Promise<void>;
    disconnect(): Promise<void>;
    [key: string]: unknown;
  }

  export class BinanceAdapter extends ExchangeClientBase {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
  }

  export class OkxAdapter extends ExchangeClientBase {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
  }

  export class BybitAdapter extends ExchangeClientBase {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
  }

  export class ExchangeFactory {
    static createExchange(name: string, config: Record<string, unknown>): IExchange;
  }

  export const exchanges: {
    Binance: new (config: Record<string, unknown>) => IExchange;
    Coinbase: new (config: Record<string, unknown>) => IExchange;
    Kraken: new (config: Record<string, unknown>) => IExchange;
  };
}

declare module '@agencyos/trading-core/arbitrage' {
  export interface ArbitrageOpportunity {
    id: string;
    symbol: string;
    buyExchange: string;
    sellExchange: string;
    spread: number;
    profit: number;
    timestamp: number;
    buyPrice: number;
    sellPrice: number;
    spreadPercent: number;
    netProfitPercent: number;
    estimatedProfitUsd: number;
    [key: string]: unknown;
  }

  export interface ArbitrageConfig {
    minProfit?: number;
    maxInvestment?: number;
    exchanges?: string[];
    symbols?: string[];
    minSpreadPercent?: number;
    pollIntervalMs?: number;
    positionSizeUsd?: number;
    [key: string]: unknown;
  }

  export interface ExchangeConfig {
    name: string;
    apiKey?: string;
    secret?: string;
    [key: string]: unknown;
  }

  export class AgiArbitrageEngine {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
    execute(): Promise<Record<string, unknown>>;
    init(): void;
    start(): void;
    stop(): void;
    getStats(): Record<string, unknown>;
    getProfitSummary(): Record<string, unknown>;
    [key: string]: unknown;
  }

  export class SpreadDetectorEngine {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
    init(): void;
    start(): void;
    stop(): void;
    getStats(): Record<string, unknown>;
    getProfitSummary(): Record<string, unknown>;
    [key: string]: unknown;
  }

  export class ArbitrageOrchestrator {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
    init(): void;
    start(): void;
    stop(): void;
    getStats(): Record<string, unknown>;
    [key: string]: unknown;
  }

  export class ArbitrageScanner {
    constructor(config?: ArbitrageConfig, ...args: unknown[]);
    scan(): Promise<ArbitrageOpportunity[]>;
    addExchange(config: ExchangeConfig | Record<string, unknown>, ...args: unknown[]): void;
    onOpportunity(callback: (opp: ArbitrageOpportunity) => void, ...args: unknown[]): void;
    start(): void;
    stop(): void;
    getStats(): Record<string, unknown>;
    [key: string]: unknown;
  }

  export class ArbitrageExecutor {
    constructor(config?: Record<string, unknown>, ...args: unknown[]);
    execute(opp: ArbitrageOpportunity): Promise<Record<string, unknown>>;
    addExchange(exchange: Record<string, unknown>, ...args: unknown[]): void;
    printDashboard(): void;
    [key: string]: unknown;
  }
}

declare module '@agencyos/trading-core/interfaces' {
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

  export interface IStrategy {
    name: string;
    execute(): Promise<Record<string, unknown>>;
    [key: string]: unknown;
  }

  export enum SignalType {
    BUY = 'buy',
    SELL = 'sell',
    HOLD = 'hold',
  }
}

declare module '@agencyos/vibe-arbitrage-engine/strategies' {
  export interface Strategy {
    name: string;
    execute(): Promise<Record<string, unknown>>;
    [key: string]: unknown;
  }

  export class CrossExchangeArbitrage implements Strategy {
    name: string;
    execute(): Promise<Record<string, unknown>>;
  }

  export class TriangularArbitrage implements Strategy {
    name: string;
    execute(): Promise<Record<string, unknown>>;
  }

  export class StatisticalArbitrage implements Strategy {
    name: string;
    execute(): Promise<Record<string, unknown>>;
  }

  export const strategies: {
    TriangularArbitrage: Strategy;
    CrossExchangeArbitrage: Strategy;
    StatisticalArbitrage: Strategy;
  };
}
