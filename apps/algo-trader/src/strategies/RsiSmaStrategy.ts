import { ISignal, SignalType } from '../interfaces/IStrategy';
import { ICandle } from '../interfaces/ICandle';
import { Indicators } from '../analysis/indicators';
import { BaseStrategy } from './BaseStrategy';
import { TECHNICAL_ANALYSIS } from '../utils/constants';

export class RsiSmaStrategy extends BaseStrategy {
  name = 'RSI + SMA Strategy';

  private readonly rsiPeriod = TECHNICAL_ANALYSIS.RSI_PERIOD;
  private readonly smaFastPeriod = TECHNICAL_ANALYSIS.SMA_SHORT_PERIOD;
  private readonly smaSlowPeriod = TECHNICAL_ANALYSIS.SMA_LONG_PERIOD;
  private readonly rsiOverbought = TECHNICAL_ANALYSIS.RSI_OVERBOUGHT;
  private readonly rsiOversold = TECHNICAL_ANALYSIS.RSI_OVERSOLD;

  constructor() {
    super();
    this.maxHistoryBuffer = 200;
  }

  async onCandle(candle: ICandle): Promise<ISignal | null> {
    this.bufferCandle(candle);

    // Need enough data
    if (this.candles.length < this.smaSlowPeriod) {
      return null;
    }

    const closes = this.getCloses();
    const rsiValues = Indicators.rsi(closes, this.rsiPeriod);
    const smaFastValues = Indicators.sma(closes, this.smaFastPeriod);
    const smaSlowValues = Indicators.sma(closes, this.smaSlowPeriod);

    const currentRsi = Indicators.getLast(rsiValues);
    const currentSmaFast = Indicators.getLast(smaFastValues);
    const currentSmaSlow = Indicators.getLast(smaSlowValues);

    // Logic:
    // BUY if SMA20 > SMA50 AND RSI < 30 (Oversold in uptrend context - dip buy)
    // SELL if RSI > 70 (Overbought)

    // Note: The logic in the plan said "Buy if SMA20 > SMA50 AND RSI < 30".
    // This is a "buy the dip in an uptrend" strategy.

    if (currentSmaFast > currentSmaSlow && currentRsi < this.rsiOversold) {
      return {
        type: SignalType.BUY,
        price: candle.close,
        timestamp: candle.timestamp,
        metadata: {
          rsi: currentRsi,
          smaFast: currentSmaFast,
          smaSlow: currentSmaSlow
        }
      };
    }

    if (currentRsi > this.rsiOverbought) {
      return {
        type: SignalType.SELL,
        price: candle.close,
        timestamp: candle.timestamp,
        metadata: {
          rsi: currentRsi
        }
      };
    }

    return null;
  }
}
