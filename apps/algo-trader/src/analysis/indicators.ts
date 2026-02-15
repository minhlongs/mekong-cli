import { RSI, SMA } from 'technicalindicators';

export class Indicators {
  /**
   * Calculate Relative Strength Index (RSI)
   * @param values Array of prices
   * @param period RSI period (default 14)
   */
  static rsi(values: number[], period: number = 14): number[] {
    return RSI.calculate({
      values,
      period,
    });
  }

  /**
   * Calculate Simple Moving Average (SMA)
   * @param values Array of prices
   * @param period SMA period
   */
  static sma(values: number[], period: number): number[] {
    return SMA.calculate({
      values,
      period,
    });
  }

  /**
   * Get the last value of an indicator array
   * @param values Indicator values
   */
  static getLast(values: number[]): number {
    if (!values || values.length === 0) return 0;
    return values[values.length - 1];
  }

  /**
   * Calculate Z-Score
   * @param value Current value
   * @param mean Mean value
   * @param stdDev Standard Deviation
   */
  static zScore(value: number, mean: number, stdDev: number): number {
    if (stdDev === 0) return 0;
    return (value - mean) / stdDev;
  }

  /**
   * Calculate Standard Deviation
   * @param values Array of numbers
   */
  static standardDeviation(values: number[]): number {
    const n = values.length;
    if (n === 0) return 0;
    const mean = values.reduce((a, b) => a + b) / n;
    return Math.sqrt(values.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / n);
  }

  /**
   * Calculate Correlation coefficient
   * @param x Array of numbers
   * @param y Array of numbers
   */
  static correlation(x: number[], y: number[]): number {
    const n = x.length;
    if (n !== y.length || n === 0) return 0;

    const meanX = x.reduce((a, b) => a + b) / n;
    const meanY = y.reduce((a, b) => a + b) / n;

    let num = 0;
    let denX = 0;
    let denY = 0;

    for (let i = 0; i < n; i++) {
      const dx = x[i] - meanX;
      const dy = y[i] - meanY;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }

    if (denX === 0 || denY === 0) return 0;
    return num / Math.sqrt(denX * denY);
  }
}
