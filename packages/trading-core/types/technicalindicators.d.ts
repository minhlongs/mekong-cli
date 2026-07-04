/**
 * Type declarations for technicalindicators package.
 * Only declares types actually used by trading-core.
 */
declare module 'technicalindicators' {
  export class RSI {
    static calculate(input: { values: number[]; period: number }): number[];
  }

  export class SMA {
    static calculate(input: { values: number[]; period: number }): number[];
  }

  export class MACD {
    static calculate(input: {
      values: number[];
      fastPeriod: number;
      slowPeriod: number;
      signalPeriod: number;
      SimpleMAOscillator?: boolean;
      SimpleMASignal?: boolean;
    }): Array<{ MACD?: number; signal?: number; histogram?: number }>;
  }

  export class BollingerBands {
    static calculate(input: {
      values: number[];
      period: number;
      stdDev: number;
    }): Array<{ middle: number; upper: number; lower: number; pb: number }>;
  }
}
