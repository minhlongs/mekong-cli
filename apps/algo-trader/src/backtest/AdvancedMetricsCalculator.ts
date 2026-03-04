/**
 * Advanced Metrics Calculator for Backtesting
 * Calculates sophisticated performance metrics including Sortino, Calmar, and Sterling ratios
 */

export interface AdvancedBacktestMetrics {
  // Return metrics
  totalReturn: number; // Total return over backtest period
  annualizedReturn: number; // Annualized return

  // Risk-adjusted metrics
  sharpeRatio: number; // Standard Sharpe ratio
  sortinoRatio: number; // Sortino ratio (downside deviation only)
  calmarRatio: number; // Calmar ratio (annualized return / max drawdown)
  sterlingRatio: number; // Sterling ratio (annualized return / avg drawdown)
  treynorRatio: number; // Treynor ratio (return per unit of systematic risk)

  // Drawdown metrics
  maxDrawdown: number; // Maximum drawdown experienced
  avgDrawdown: number; // Average drawdown
  drawdownDuration: number; // Average duration of drawdowns
  recoveryFactor: number; // Return divided by max drawdown (abs)

  // Volatility metrics
  volatility: number; // Annualized standard deviation
  downsideDeviation: number; // Downside deviation (for Sortino)

  // Performance metrics
  winRate: number; // Percentage of profitable trades
  profitFactor: number; // Gross profit / gross loss
  expectancy: number; // Expected value per dollar risked
  ulcerIndex: number; // Ulcer index (weighted drawdowns)
  tailRatio: number; // Ratio of 95th percentile gain to 5th percentile loss

  // Efficiency metrics
  profitPerDay: number; // Average profit per day
  riskRewardRatio: number; // Average reward/risk ratio
  bestTrade: number; // Best trade return %
  worstTrade: number; // Worst trade return %
  avgWin: number; // Average winning trade %
  avgLoss: number; // Average losing trade %
}

export interface DrawdownPeriod {
  peak: number;
  trough: number;
  start: Date;
  end: Date;
  drawdown: number; // As percentage
}

export interface Trade {
  entryPrice: number;
  exitPrice: number;
  entryTime: number;
  exitTime: number;
  profit: number;
  profitPercent: number;
  positionSize: number;
  fees: number;
}

export class AdvancedMetricsCalculator {
  /**
   * Calculate advanced performance metrics for backtesting
   * @param trades Array of completed trades
   * @param equityCurve Equity curve over time (portfolio value at each point)
   * @param riskFreeRate Annual risk-free rate (default: 0.02 or 2%)
   * @returns Advanced backtesting metrics
   */
  static calculateMetrics(
    trades: Trade[],
    equityCurve: number[],
    riskFreeRate: number = 0.02
  ): AdvancedBacktestMetrics {
    if (trades.length === 0) {
      return this.getDefaultMetrics();
    }

    // Calculate basic return metrics
    const totalReturn = this.calculateTotalReturn(equityCurve);
    const dailyReturns = this.calculateDailyReturns(equityCurve);
    const tradingDays = this.estimateTradingDays(equityCurve.length);

    // Calculate annualized return
    const years = tradingDays / 252; // 252 trading days in a year
    const annualizedReturn = years > 0 ? Math.pow(1 + totalReturn / 100, 1 / years) - 1 : 0;

    // Calculate volatility
    const volatility = this.calculateVolatility(dailyReturns);
    const annualizedVolatility = volatility * Math.sqrt(252);

    // Calculate risk-adjusted metrics
    const sharpeRatio = this.calculateSharpeRatio(dailyReturns, riskFreeRate / 252, annualizedVolatility);
    const sortinoRatio = this.calculateSortinoRatio(dailyReturns, riskFreeRate / 252);
    const { maxDrawdown, drawdowns } = this.calculateMaxDrawdown(equityCurve);
    const calmarRatio = maxDrawdown !== 0 ? annualizedReturn / Math.abs(maxDrawdown) : 0;

    // Calculate average drawdown
    const avgDrawdown = this.calculateAverageDrawdown(drawdowns);
    const sterlingRatio = avgDrawdown !== 0 ? annualizedReturn / Math.abs(avgDrawdown) : 0;

    // Calculate profit factor and other trade metrics
    const { winRate, profitFactor, avgWin, avgLoss, expectancy, riskRewardRatio } =
      this.calculateTradeMetrics(trades);

    // Calculate tail ratio
    const tailRatio = this.calculateTailRatio(dailyReturns);

    // Calculate ulcer index
    const ulcerIndex = this.calculateUlcerIndex(equityCurve);

    // Calculate recovery factor
    const recoveryFactor = maxDrawdown !== 0 ? totalReturn / Math.abs(maxDrawdown) : 0;

    // Calculate best and worst trades
    const bestTrade = trades.length > 0 ? Math.max(...trades.map(t => t.profitPercent)) : 0;
    const worstTrade = trades.length > 0 ? Math.min(...trades.map(t => t.profitPercent)) : 0;

    // Calculate drawdown duration (average length of drawdown periods)
    const drawdownDuration = this.calculateAverageDrawdownDuration(drawdowns);

    return {
      totalReturn,
      annualizedReturn,
      sharpeRatio,
      sortinoRatio,
      calmarRatio,
      sterlingRatio,
      treynorRatio: 0, // Treynor requires market data
      maxDrawdown,
      avgDrawdown,
      drawdownDuration,
      recoveryFactor,
      volatility: annualizedVolatility,
      downsideDeviation: this.calculateDownsideDeviation(dailyReturns) * Math.sqrt(252),
      winRate,
      profitFactor,
      expectancy,
      ulcerIndex,
      tailRatio,
      profitPerDay: totalReturn / tradingDays,
      riskRewardRatio,
      bestTrade,
      worstTrade,
      avgWin,
      avgLoss
    };
  }

  private static getDefaultMetrics(): AdvancedBacktestMetrics {
    return {
      totalReturn: 0,
      annualizedReturn: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      calmarRatio: 0,
      sterlingRatio: 0,
      treynorRatio: 0,
      maxDrawdown: 0,
      avgDrawdown: 0,
      drawdownDuration: 0,
      recoveryFactor: 0,
      volatility: 0,
      downsideDeviation: 0,
      winRate: 0,
      profitFactor: 0,
      expectancy: 0,
      ulcerIndex: 0,
      tailRatio: 0,
      profitPerDay: 0,
      riskRewardRatio: 0,
      bestTrade: 0,
      worstTrade: 0,
      avgWin: 0,
      avgLoss: 0
    };
  }

  private static calculateTotalReturn(equityCurve: number[]): number {
    if (equityCurve.length < 2) return 0;
    return ((equityCurve[equityCurve.length - 1] - equityCurve[0]) / equityCurve[0]) * 100;
  }

  private static calculateDailyReturns(equityCurve: number[]): number[] {
    const returns: number[] = [];
    for (let i = 1; i < equityCurve.length; i++) {
      if (equityCurve[i - 1] !== 0) {
        returns.push((equityCurve[i] - equityCurve[i - 1]) / equityCurve[i - 1]);
      }
    }
    return returns;
  }

  private static estimateTradingDays(dataPoints: number): number {
    // Assuming daily data points, adjust based on actual frequency
    // This is a simple estimation - real implementation might need to account for weekends/holidays
    return dataPoints;
  }

  private static calculateVolatility(dailyReturns: number[]): number {
    if (dailyReturns.length < 2) return 0;

    const mean = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
    const squaredDeviations = dailyReturns.map(ret => Math.pow(ret - mean, 2));
    const variance = squaredDeviations.reduce((sum, sq) => sum + sq, 0) / (dailyReturns.length - 1);
    return Math.sqrt(variance);
  }

  private static calculateSharpeRatio(dailyReturns: number[], dailyRiskFreeRate: number, annualizedVolatility: number): number {
    if (annualizedVolatility === 0 || dailyReturns.length === 0) return 0;

    const dailyMeanReturn = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
    const excessReturn = dailyMeanReturn - dailyRiskFreeRate;
    const annualizedExcessReturn = excessReturn * 252;

    return annualizedExcessReturn / annualizedVolatility;
  }

  private static calculateSortinoRatio(dailyReturns: number[], dailyRiskFreeRate: number): number {
    if (dailyReturns.length === 0) return 0;

    const dailyMeanReturn = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
    const excessReturn = dailyMeanReturn - dailyRiskFreeRate;
    const annualizedExcessReturn = excessReturn * 252;

    const downsideDeviation = this.calculateDownsideDeviation(dailyReturns);
    const annualizedDownsideDeviation = downsideDeviation * Math.sqrt(252);

    if (annualizedDownsideDeviation === 0) return 0;
    return annualizedExcessReturn / annualizedDownsideDeviation;
  }

  private static calculateDownsideDeviation(dailyReturns: number[]): number {
    if (dailyReturns.length === 0) return 0;

    const mean = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
    const squaredDownsideDeviations = dailyReturns
      .filter(ret => ret < mean) // Only downside deviations
      .map(ret => Math.pow(ret - mean, 2));

    if (squaredDownsideDeviations.length === 0) return 0;

    const meanSquaredDownside = squaredDownsideDeviations.reduce((sum, sq) => sum + sq, 0) / squaredDownsideDeviations.length;
    return Math.sqrt(meanSquaredDownside);
  }

  private static calculateMaxDrawdown(equityCurve: number[]): { maxDrawdown: number; drawdowns: DrawdownPeriod[] } {
    if (equityCurve.length === 0) {
      return { maxDrawdown: 0, drawdowns: [] };
    }

    let peak = equityCurve[0];
    let currentDrawdown = 0;
    let maxDrawdown = 0;
    const drawdowns: DrawdownPeriod[] = [];

    let drawdownStart: number | null = null;

    for (let i = 1; i < equityCurve.length; i++) {
      if (equityCurve[i] > peak) {
        peak = equityCurve[i];

        // If we were in a drawdown, record it
        if (drawdownStart !== null && i - 1 > drawdownStart) {
          const trough = Math.min(...equityCurve.slice(drawdownStart, i));
          const drawdown = ((peak - trough) / peak) * 100;

          drawdowns.push({
            peak,
            trough,
            start: new Date(drawdownStart),
            end: new Date(i),
            drawdown
          });

          drawdownStart = null;
        }
      }

      currentDrawdown = ((peak - equityCurve[i]) / peak) * 100;
      maxDrawdown = Math.max(maxDrawdown, currentDrawdown);

      // Start recording a drawdown period
      if (currentDrawdown > 0 && drawdownStart === null) {
        drawdownStart = i;
      }
    }

    // If we're still in a drawdown at the end, record it
    if (drawdownStart !== null && equityCurve.length - 1 > drawdownStart) {
      const trough = Math.min(...equityCurve.slice(drawdownStart, equityCurve.length));
      const drawdown = ((peak - trough) / peak) * 100;

      drawdowns.push({
        peak,
        trough,
        start: new Date(drawdownStart),
        end: new Date(equityCurve.length - 1),
        drawdown
      });
    }

    return { maxDrawdown, drawdowns };
  }

  private static calculateAverageDrawdown(drawdowns: DrawdownPeriod[]): number {
    if (drawdowns.length === 0) return 0;
    const sum = drawdowns.reduce((acc, dd) => acc + dd.drawdown, 0);
    return sum / drawdowns.length;
  }

  private static calculateAverageDrawdownDuration(drawdowns: DrawdownPeriod[]): number {
    if (drawdowns.length === 0) return 0;

    const durations = drawdowns.map(dd => (dd.end.getTime() - dd.start.getTime()) / (1000 * 60 * 60 * 24)); // Convert to days
    return durations.reduce((sum, dur) => sum + dur, 0) / durations.length;
  }

  private static calculateTradeMetrics(trades: Trade[]): {
    winRate: number;
    profitFactor: number;
    avgWin: number;
    avgLoss: number;
    expectancy: number;
    riskRewardRatio: number;
  } {
    if (trades.length === 0) {
      return {
        winRate: 0,
        profitFactor: 0,
        avgWin: 0,
        avgLoss: 0,
        expectancy: 0,
        riskRewardRatio: 0
      };
    }

    const winningTrades = trades.filter(t => t.profit > 0);
    const losingTrades = trades.filter(t => t.profit < 0);

    const totalWinning = winningTrades.reduce((sum, t) => sum + t.profit, 0);
    const totalLosing = Math.abs(losingTrades.reduce((sum, t) => sum + t.profit, 0));

    const winRate = (winningTrades.length / trades.length) * 100;
    const profitFactor = totalLosing !== 0 ? totalWinning / totalLosing : 0;
    const avgWin = winningTrades.length > 0 ? totalWinning / winningTrades.length : 0;
    const avgLoss = losingTrades.length > 0 ? totalLosing / losingTrades.length : 0;

    // Expectancy = (avgWin * winRate) - (avgLoss * (1 - winRate))
    const winProb = winRate / 100;
    const lossProb = 1 - winProb;
    const expectancy = (avgWin * winProb) - (avgLoss * lossProb);

    // Risk/Reward ratio = avgWin / avgLoss
    const riskRewardRatio = avgLoss !== 0 ? avgWin / avgLoss : 0;

    return {
      winRate,
      profitFactor,
      avgWin,
      avgLoss,
      expectancy,
      riskRewardRatio
    };
  }

  private static calculateTailRatio(dailyReturns: number[]): number {
    if (dailyReturns.length === 0) return 0;

    // Sort returns
    const sortedReturns = [...dailyReturns].sort((a, b) => a - b);
    const n = sortedReturns.length;

    // Get 95th percentile (top 5%) and 5th percentile (bottom 5%)
    const topPercentileIndex = Math.floor(0.95 * n);
    const bottomPercentileIndex = Math.floor(0.05 * n);

    const top5Percent = sortedReturns[topPercentileIndex];
    const bottom5Percent = sortedReturns[bottomPercentileIndex];

    // Tail ratio = top / abs(bottom)
    return bottom5Percent !== 0 ? top5Percent / Math.abs(bottom5Percent) : 0;
  }

  private static calculateUlcerIndex(equityCurve: number[]): number {
    if (equityCurve.length === 0) return 0;

    // Find the high watermarks for each point
    const highWatermarks: number[] = [];
    let currentHigh = equityCurve[0];
    for (const value of equityCurve) {
      if (value > currentHigh) {
        currentHigh = value;
      }
      highWatermarks.push(currentHigh);
    }

    // Calculate the percentage drawdown for each point
    const squaredDrawdowns = equityCurve.map((value, i) => {
      const drawdown = ((highWatermarks[i] - value) / highWatermarks[i]) * 100;
      return drawdown * drawdown;
    });

    // Calculate average squared drawdown and take the square root
    const averageSquaredDrawdown = squaredDrawdowns.reduce((sum, sq) => sum + sq, 0) / squaredDrawdowns.length;
    return Math.sqrt(averageSquaredDrawdown);
  }
}