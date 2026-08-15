declare module '@agencyos/trading-core' {
  export class BinanceAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class OkxAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class BybitAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class SpreadDetectorEngine {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ExchangeConfig {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ExchangeClientBase {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export type IOrder = any;
  export type IBalance = any;
  export type IOrderBookEntry = any;
  export type IOrderBook = any;
  export type IExchange = any;
}

declare module '@agencyos/trading-core/exchanges' {
  export class BinanceAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class OkxAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class BybitAdapter {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ExchangeClientBase {
    [key: string]: any;
    constructor(...args: any[]);
  }
}

declare module '@agencyos/trading-core/arbitrage' {
  export class SpreadDetectorEngine {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ExchangeConfig {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class AgiArbitrageEngine {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ArbitrageOrchestrator {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ArbitrageScanner {
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class ArbitrageExecutor {
    [key: string]: any;
    constructor(...args: any[]);
  }
}

declare module '@agencyos/trading-core/interfaces' {
  export type IOrder = any;
  export type IBalance = any;
  export type IOrderBookEntry = any;
  export type IOrderBook = any;
  export type IExchange = any;
}
