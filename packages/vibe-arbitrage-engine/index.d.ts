declare module '@agencyos/vibe-arbitrage-engine' {
  export class CrossExchangeArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class TriangularArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class StatisticalArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
}

declare module '@agencyos/vibe-arbitrage-engine/strategies' {
  export class CrossExchangeArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class TriangularArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
  export class StatisticalArbitrage {
    name: string;
    init(...args: any[]): any;
    onCandle(...args: any[]): any;
    [key: string]: any;
    constructor(...args: any[]);
  }
}
