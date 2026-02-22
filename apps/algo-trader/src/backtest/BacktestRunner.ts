import { IStrategy, SignalType } from '../interfaces/IStrategy';
import { IDataProvider } from '../interfaces/IDataProvider';
import { ICandle } from '../interfaces/ICandle';

import { logger } from '../utils/logger';

interface Trade {
  entryPrice: number;
  exitPrice: number;
  entryTime: number;
  exitTime: number;
  profit: number;
  profitPercent: number;
}

export class BacktestRunner {
  private strategy: IStrategy;
  private dataProvider: IDataProvider;
  private initialBalance: number;
  private balance: number;
  private trades: Trade[] = [];
  private openPosition: { price: number; time: number } | null = null;

  constructor(strategy: IStrategy, dataProvider: IDataProvider, initialBalance: number = 10000) {
    this.strategy = strategy;
    this.dataProvider = dataProvider;
    this.initialBalance = initialBalance;
    this.balance = initialBalance;
  }

  async run(days: number = 30): Promise<void> {
    logger.info(`Starting backtest for ${this.strategy.name} over ${days} days...`);

    // 1. Get History
    const limit = days * 24 * 60; // Minutes
    const history = await this.dataProvider.getHistory(limit);

    if (history.length === 0) {
      logger.info('No data available for backtest');
      return;
    }

    logger.info(`Loaded ${history.length} candles.`);

    // 2. Init Strategy
    await this.strategy.init(history.slice(0, 200)); // Warmup with first 200

    // 3. Iterate through history
    for (let i = 200; i < history.length; i++) {
      const candle = history[i];
      const signal = await this.strategy.onCandle(candle);

      if (signal) {
        if (signal.type === SignalType.BUY && !this.openPosition) {
          this.executeBuy(candle);
        } else if (signal.type === SignalType.SELL && this.openPosition) {
          this.executeSell(candle);
        }
      }
    }

    this.printResults();
  }

  private executeBuy(candle: ICandle) {
    this.openPosition = {
      price: candle.close,
      time: candle.timestamp
    };
    // console.log(`[BUY] @ ${candle.close} on ${new Date(candle.timestamp).toISOString()}`);
  }

  private executeSell(candle: ICandle) {
    if (!this.openPosition) return;

    const entryPrice = this.openPosition.price;
    const exitPrice = candle.close;
    const profit = exitPrice - entryPrice; // Simplified: 1 unit per trade for backtest
    const profitPercent = (profit / entryPrice) * 100;

    this.trades.push({
      entryPrice,
      exitPrice,
      entryTime: this.openPosition.time,
      exitTime: candle.timestamp,
      profit,
      profitPercent
    });

    this.balance += profit;
    this.openPosition = null;
    // console.log(`[SELL] @ ${candle.close} on ${new Date(candle.timestamp).toISOString()} | PnL: ${profit.toFixed(2)} (${profitPercent.toFixed(2)}%)`);
  }

  private printResults() {
    const wins = this.trades.filter(t => t.profit > 0).length;
    const losses = this.trades.length - wins;
    const winRate = this.trades.length > 0 ? (wins / this.trades.length) * 100 : 0;
    const totalReturn = ((this.balance - this.initialBalance) / this.initialBalance) * 100;

    logger.info('\n--- Backtest Results ---');
    logger.info(`Initial Balance: ${this.initialBalance}`);
    logger.info(`Final Balance:   ${this.balance.toFixed(2)}`);
    logger.info(`Return:          ${totalReturn.toFixed(2)}%`);
    logger.info(`Total Trades:    ${this.trades.length}`);
    logger.info(`Wins:            ${wins}`);
    logger.info(`Losses:          ${losses}`);
    logger.info(`Win Rate:        ${winRate.toFixed(2)}%`);
    logger.info('------------------------\n');
  }
}
