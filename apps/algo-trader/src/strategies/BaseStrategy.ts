import { IStrategy, ISignal, SignalType } from '../interfaces/IStrategy';
import { ICandle } from '../interfaces/ICandle';

export abstract class BaseStrategy implements IStrategy {
  abstract name: string;
  protected candles: ICandle[] = [];
  protected maxHistoryBuffer: number = 200; // Default buffer size

  /**
   * Initialize the strategy with historical data.
   * Can be overridden by subclasses if needed.
   * @param history Array of historical candles
   */
  async init(history: ICandle[]): Promise<void> {
    this.candles = [...history];
    // Trim history to max buffer if it exceeds
    if (this.candles.length > this.maxHistoryBuffer) {
      this.candles = this.candles.slice(-this.maxHistoryBuffer);
    }
  }

  /**
   * Buffer the new candle and ensure we don't exceed the memory limit
   * @param candle The new candle
   */
  protected bufferCandle(candle: ICandle): void {
    this.candles.push(candle);
    if (this.candles.length > this.maxHistoryBuffer) {
      this.candles.shift();
    }
  }

  /**
   * Extract closing prices from the current buffered candles
   * @returns Array of closing prices
   */
  protected getCloses(): number[] {
    return this.candles.map(c => c.close);
  }

  /**
   * Process a new candle. Must be implemented by subclasses.
   * Usually begins with `this.bufferCandle(candle);`
   * @param candle The new candle
   */
  abstract onCandle(candle: ICandle): Promise<ISignal | null>;
}