import * as chalk from 'chalk';
import { PerformanceMetrics } from './PerformanceAnalyzer';

export class ConsoleReporter {
  static report(metrics: PerformanceMetrics) {
    console.log(chalk.bold.blue('\n=== Performance Report ==='));
    console.log(`Total Trades:   ${metrics.totalTrades}`);
    console.log(`Win Rate:       ${this.colorValue(metrics.winRate, 50, '%')}`);
    console.log(`Total Return:   ${this.colorValue(metrics.totalReturn, 0, '%')}`);
    console.log(`Profit Factor:  ${metrics.profitFactor.toFixed(2)}`);
    console.log(`Max Drawdown:   ${chalk.red(metrics.maxDrawdown.toFixed(2) + '%')}`);
    console.log(`Sharpe Ratio:   ${metrics.sharpeRatio.toFixed(3)}`);
    console.log(`Avg Win:        ${chalk.green(metrics.averageWin.toFixed(2))}`);
    console.log(`Avg Loss:       ${chalk.red(metrics.averageLoss.toFixed(2))}`);
    console.log('==========================\n');
  }

  private static colorValue(value: number, threshold: number, suffix: string = ''): string {
    const formatted = value.toFixed(2) + suffix;
    return value >= threshold ? chalk.green(formatted) : chalk.red(formatted);
  }
}
