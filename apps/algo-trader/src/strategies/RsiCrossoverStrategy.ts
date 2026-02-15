import { IStrategy, ISignal, SignalType } from '../interfaces/IStrategy';
import { ICandle } from '../interfaces/ICandle';
import { Indicators } from '../analysis/indicators';

export class RsiCrossoverStrategy implements IStrategy {
  name = 'RSI Crossover Strategy';
  private candles: ICandle[] = [];
  private prevRsi: number | null = null;

  private readonly rsiPeriod = 14;
  private readonly rsiOverbought = 70;
  private readonly rsiOversold = 30;

  async init(history: ICandle[]): Promise<void> {
    this.candles = [...history];
    const closes = this.candles.map(c => c.close);
    const rsiValues = Indicators.rsi(closes, this.rsiPeriod);
    this.prevRsi = Indicators.getLast(rsiValues);
  }

  async onCandle(candle: ICandle): Promise<ISignal | null> {
    this.candles.push(candle);

    // Giữ lịch sử tối thiểu để tính toán (khoảng 200 nến là đủ cho RSI 14)
    if (this.candles.length > 200) {
      this.candles.shift();
    }

    const closes = this.candles.map(c => c.close);
    const rsiValues = Indicators.rsi(closes, this.rsiPeriod);
    const currentRsi = Indicators.getLast(rsiValues);

    let signal: ISignal | null = null;

    if (this.prevRsi !== null) {
      // Mua khi RSI cắt LÊN trên vùng quá bán (30)
      if (this.prevRsi < this.rsiOversold && currentRsi >= this.rsiOversold) {
        signal = {
          type: SignalType.BUY,
          price: candle.close,
          timestamp: candle.timestamp,
          metadata: {
            rsi: currentRsi,
            prevRsi: this.prevRsi,
            condition: 'oversold_crossover_up'
          }
        };
      }
      // Bán khi RSI cắt XUỐNG dưới vùng quá mua (70)
      else if (this.prevRsi > this.rsiOverbought && currentRsi <= this.rsiOverbought) {
        signal = {
          type: SignalType.SELL,
          price: candle.close,
          timestamp: candle.timestamp,
          metadata: {
            rsi: currentRsi,
            prevRsi: this.prevRsi,
            condition: 'overbought_crossover_down'
          }
        };
      }
    }

    this.prevRsi = currentRsi;
    return signal;
  }
}
