import { ICandle } from './ICandle';

export enum SignalType {
  BUY = 'BUY',
  SELL = 'SELL',
  NONE = 'NONE'
}

export interface ISignal {
  type: SignalType;
  price: number;
  timestamp: number;
  tag?: string;
  metadata?: Record<string, unknown>;
}

export interface IStrategy {
  name: string;

  /**
   * Update the strategy with a new candle
   * @param candle The new candle
   * @returns A signal if one is generated, otherwise null
   */
  onCandle(candle: ICandle): Promise<ISignal | null>;

  /**
   * Initialize the strategy with historical data
   * @param history Array of historical candles
   */
  init(history: ICandle[]): Promise<void>;
}
