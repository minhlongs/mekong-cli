/**
 * BacktestEngine — Advanced backtesting framework.
 * Walk-forward analysis, equity curve tracking, Monte Carlo simulation.
 * Builds on BacktestRunner with portfolio-level and robustness features.
 */

import { IStrategy, SignalType } from '../interfaces/IStrategy';
import { ICandle } from '../interfaces/ICandle';
import { BacktestResult, BacktestConfig } from './BacktestRunner';
import { logger } from '../utils/logger';

export interface EquityPoint {
  timestamp: number;
  equity: number;
  drawdown: number; // Current drawdown %
}

export interface DetailedTrade {
  entryPrice: number;
  exitPrice: number;
  entryTime: number;
  exitTime: number;
  profit: number;
  profitPercent: number;
  positionSize: number;
  fees: number;
  holdingPeriodMs: number;
  maxAdverseExcursion: number; // Worst price during trade
  maxFavorableExcursion: number; // Best price during trade
}

export interface WalkForwardWindow {
  trainStart: number;
  trainEnd: number;
  testStart: number;
  testEnd: number;
  trainResult: BacktestResult;
  testResult: BacktestResult;
}

export interface WalkForwardResult {
  windows: WalkForwardWindow[];
  aggregateTestReturn: number;
  aggregateTestSharpe: number;
  robustnessRatio: number; // test_sharpe / train_sharpe — closer to 1 = more robust
  overfit: boolean; // true if test performance degrades >50% vs train
}

export interface MonteCarloResult {
  medianReturn: number;
  p5Return: number;    // 5th percentile (worst case)
  p95Return: number;   // 95th percentile (best case)
  medianDrawdown: number;
  p95Drawdown: number; // 95th percentile worst drawdown
  ruinProbability: number; // % of simulations that lost >50%
}

export interface EngineResult extends BacktestResult {
  equityCurve: EquityPoint[];
  detailedTrades: DetailedTrade[];
  calmarRatio: number;    // Annual return / max drawdown
  sortinoRatio: number;   // Return / downside deviation
  expectancy: number;     // Avg win * win_rate - avg loss * loss_rate
}

export class BacktestEngine {
  private feeRate: number;
  private riskPercentage: number;
  private slippageBps: number;

  constructor(config?: BacktestConfig) {
    this.feeRate = config?.feeRate ?? 0.001;
    this.riskPercentage = config?.riskPercentage ?? 2;
    this.slippageBps = config?.slippageBps ?? 5;
  }

  /**
   * Run a detailed backtest with equity curve and advanced metrics.
   */
  async runDetailed(
    strategy: IStrategy,
    candles: ICandle[],
    initialBalance = 10000
  ): Promise<EngineResult> {
    let balance = initialBalance;
    let peakBalance = initialBalance;
    let maxDrawdown = 0;
    const trades: DetailedTrade[] = [];
    const equityCurve: EquityPoint[] = [];
    let openPos: { price: number; time: number; size: number; mae: number; mfe: number } | null = null;

    const warmup = Math.min(200, Math.floor(candles.length * 0.1));
    if (candles.length <= warmup) {
      return this.emptyResult(strategy.name, initialBalance);
    }

    await strategy.init(candles.slice(0, warmup));

    for (let i = warmup; i < candles.length; i++) {
      const candle = candles[i];

      // Track MAE/MFE for open positions
      if (openPos) {
        openPos.mae = Math.min(openPos.mae, candle.low);
        openPos.mfe = Math.max(openPos.mfe, candle.high);
      }

      const signal = await strategy.onCandle(candle);

      if (signal) {
        if (signal.type === SignalType.BUY && !openPos) {
          const fillPrice = this.applySlippage(candle.close, 'buy');
          const riskAmount = balance * (this.riskPercentage / 100);
          const size = riskAmount / fillPrice;
          if (size > 0) {
            balance -= size * fillPrice * this.feeRate;
            openPos = { price: fillPrice, time: candle.timestamp, size, mae: candle.low, mfe: candle.high };
          }
        } else if (signal.type === SignalType.SELL && openPos) {
          const exitPrice = this.applySlippage(candle.close, 'sell');
          const trade = this.closeTrade(openPos, exitPrice, candle.timestamp);
          trades.push(trade);
          balance += trade.profit;
          openPos = null;
        }
      }

      // Track equity
      if (balance > peakBalance) peakBalance = balance;
      const dd = peakBalance > 0 ? ((peakBalance - balance) / peakBalance) * 100 : 0;
      if (dd > maxDrawdown) maxDrawdown = dd;

      // Sample equity curve (every 100 candles to keep output manageable)
      if (i % 100 === 0 || i === candles.length - 1) {
        equityCurve.push({ timestamp: candle.timestamp, equity: balance, drawdown: dd });
      }
    }

    return this.buildResult(strategy.name, initialBalance, balance, maxDrawdown, trades, equityCurve);
  }

  /**
   * Walk-forward analysis: split data into train/test windows,
   * run backtest on each, measure out-of-sample robustness.
   */
  async walkForward(
    strategyFactory: () => IStrategy,
    candles: ICandle[],
    windows = 5,
    trainRatio = 0.7,
    initialBalance = 10000
  ): Promise<WalkForwardResult> {
    const totalCandles = candles.length;
    const windowSize = Math.floor(totalCandles / windows);

    if (windowSize < 400) {
      logger.warn(`[WalkForward] Window size ${windowSize} too small. Need >= 400 candles per window.`);
      return { windows: [], aggregateTestReturn: 0, aggregateTestSharpe: 0, robustnessRatio: 0, overfit: true };
    }

    const results: WalkForwardWindow[] = [];
    let totalTestReturn = 0;
    let totalTrainSharpe = 0;
    let totalTestSharpe = 0;

    for (let w = 0; w < windows; w++) {
      const start = w * windowSize;
      const end = Math.min(start + windowSize, totalCandles);
      const splitIdx = start + Math.floor((end - start) * trainRatio);

      const trainData = candles.slice(start, splitIdx);
      const testData = candles.slice(splitIdx, end);

      const trainStrategy = strategyFactory();
      const trainResult = await this.runDetailed(trainStrategy, trainData, initialBalance);

      const testStrategy = strategyFactory();
      const testResult = await this.runDetailed(testStrategy, testData, initialBalance);

      results.push({
        trainStart: start,
        trainEnd: splitIdx,
        testStart: splitIdx,
        testEnd: end,
        trainResult,
        testResult,
      });

      totalTestReturn += testResult.totalReturn;
      totalTrainSharpe += trainResult.sharpeRatio;
      totalTestSharpe += testResult.sharpeRatio;
    }

    const avgTrainSharpe = totalTrainSharpe / windows;
    const avgTestSharpe = totalTestSharpe / windows;
    const robustnessRatio = avgTrainSharpe !== 0 ? avgTestSharpe / avgTrainSharpe : 0;
    const overfit = robustnessRatio < 0.5;

    return {
      windows: results,
      aggregateTestReturn: totalTestReturn / windows,
      aggregateTestSharpe: avgTestSharpe,
      robustnessRatio,
      overfit,
    };
  }

  /**
   * Monte Carlo simulation: shuffle trades to test strategy robustness.
   * Answers "would this strategy still work if trades happened in a different order?"
   */
  monteCarlo(trades: DetailedTrade[], initialBalance: number, simulations = 1000): MonteCarloResult {
    if (trades.length === 0) {
      return { medianReturn: 0, p5Return: 0, p95Return: 0, medianDrawdown: 0, p95Drawdown: 0, ruinProbability: 0 };
    }

    const finalReturns: number[] = [];
    const maxDrawdowns: number[] = [];

    for (let sim = 0; sim < simulations; sim++) {
      const shuffled = this.shuffleArray([...trades]);
      let balance = initialBalance;
      let peak = initialBalance;
      let maxDD = 0;

      for (const trade of shuffled) {
        balance += trade.profit;
        if (balance > peak) peak = balance;
        const dd = peak > 0 ? ((peak - balance) / peak) * 100 : 0;
        if (dd > maxDD) maxDD = dd;
      }

      finalReturns.push(((balance - initialBalance) / initialBalance) * 100);
      maxDrawdowns.push(maxDD);
    }

    finalReturns.sort((a, b) => a - b);
    maxDrawdowns.sort((a, b) => a - b);

    const ruinCount = finalReturns.filter(r => r < -50).length;

    return {
      medianReturn: finalReturns[Math.floor(simulations / 2)],
      p5Return: finalReturns[Math.floor(simulations * 0.05)],
      p95Return: finalReturns[Math.floor(simulations * 0.95)],
      medianDrawdown: maxDrawdowns[Math.floor(simulations / 2)],
      p95Drawdown: maxDrawdowns[Math.floor(simulations * 0.95)],
      ruinProbability: (ruinCount / simulations) * 100,
    };
  }

  private closeTrade(
    pos: { price: number; time: number; size: number; mae: number; mfe: number },
    exitPrice: number,
    exitTime: number
  ): DetailedTrade {
    const entryFee = pos.size * pos.price * this.feeRate;
    const exitFee = pos.size * exitPrice * this.feeRate;
    const grossProfit = (exitPrice - pos.price) * pos.size;
    const netProfit = grossProfit - exitFee;

    return {
      entryPrice: pos.price,
      exitPrice,
      entryTime: pos.time,
      exitTime,
      profit: netProfit,
      profitPercent: (netProfit / (pos.price * pos.size)) * 100,
      positionSize: pos.size,
      fees: entryFee + exitFee,
      holdingPeriodMs: exitTime - pos.time,
      maxAdverseExcursion: pos.mae,
      maxFavorableExcursion: pos.mfe,
    };
  }

  private buildResult(
    strategyName: string,
    initialBalance: number,
    finalBalance: number,
    maxDrawdown: number,
    trades: DetailedTrade[],
    equityCurve: EquityPoint[]
  ): EngineResult {
    const wins = trades.filter(t => t.profit > 0);
    const losses = trades.filter(t => t.profit <= 0);
    const totalReturn = ((finalBalance - initialBalance) / initialBalance) * 100;
    const totalFees = trades.reduce((s, t) => s + t.fees, 0);
    const avgProfit = trades.length > 0 ? trades.reduce((s, t) => s + t.profit, 0) / trades.length : 0;

    // Sharpe ratio
    const returns = trades.map(t => t.profitPercent / 100);
    let sharpe = 0;
    if (returns.length >= 2) {
      const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
      const variance = returns.reduce((s, r) => s + (r - mean) ** 2, 0) / (returns.length - 1);
      const std = Math.sqrt(variance);
      if (std > 0) sharpe = (mean * 252 - 0.05) / (std * Math.sqrt(252));
    }

    // Sortino: only downside deviation
    const negReturns = returns.filter(r => r < 0);
    let sortino = 0;
    if (negReturns.length >= 2) {
      const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
      const downVariance = negReturns.reduce((s, r) => s + r ** 2, 0) / negReturns.length;
      const downDev = Math.sqrt(downVariance);
      if (downDev > 0) sortino = (mean * 252 - 0.05) / (downDev * Math.sqrt(252));
    }

    // Calmar: annual return / max drawdown
    const calmar = maxDrawdown > 0 ? totalReturn / maxDrawdown : 0;

    // Expectancy
    const avgWin = wins.length > 0 ? wins.reduce((s, t) => s + t.profit, 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((s, t) => s + t.profit, 0)) / losses.length : 0;
    const winRate = trades.length > 0 ? wins.length / trades.length : 0;
    const expectancy = avgWin * winRate - avgLoss * (1 - winRate);

    return {
      strategyName,
      initialBalance,
      finalBalance,
      totalReturn,
      maxDrawdown,
      totalFees,
      totalTrades: trades.length,
      wins: wins.length,
      losses: losses.length,
      winRate: winRate * 100,
      avgProfit,
      sharpeRatio: sharpe,
      equityCurve,
      detailedTrades: trades,
      calmarRatio: calmar,
      sortinoRatio: sortino,
      expectancy,
    };
  }

  private applySlippage(price: number, side: 'buy' | 'sell'): number {
    const mul = this.slippageBps / 10000;
    return side === 'buy' ? price * (1 + mul) : price * (1 - mul);
  }

  private shuffleArray<T>(arr: T[]): T[] {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  private emptyResult(name: string, balance: number): EngineResult {
    return {
      strategyName: name, initialBalance: balance, finalBalance: balance,
      totalReturn: 0, maxDrawdown: 0, totalFees: 0, totalTrades: 0,
      wins: 0, losses: 0, winRate: 0, avgProfit: 0, sharpeRatio: 0,
      equityCurve: [], detailedTrades: [], calmarRatio: 0, sortinoRatio: 0, expectancy: 0,
    };
  }
}
