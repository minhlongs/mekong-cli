/**
 * Algo Trader - Main entry point
 * Algorithmic trading platform
 */

import { Command } from 'commander';
import { runGruStrategy } from './commands/gru-strategy';

export const version = '1.0.0';

export function main(): void {
  console.log(`Algo Trader v${version} started`);
}

// CLI setup - only run in non-test environment
const isTest = process.env.NODE_ENV === 'test' || process.argv.includes('vitest');

if (!isTest) {
  const program = new Command();

  program
    .name('algo-trader')
    .description('Algorithmic trading bot with ML strategies')
    .version(version);

  program
    .command('gru')
    .description('Run GRU Neural Network trading strategy')
    .option('-i, --input-steps <number>', 'Number of historical candles', '60')
    .option('-u, --gru-units <number>', 'GRU layer units', '64')
    .option('-e, --epochs <number>', 'Training epochs', '50')
    .option('-t, --threshold <number>', 'Confidence threshold (0-1)', '0.7')
    .option('-s, --symbol <symbol>', 'Trading pair', 'BTC/USDT')
    .option('-m, --mode <mode>', 'Running mode (live/backtest)', 'backtest')
    .action(async (options: any) => {
      await runGruStrategy({
        inputSteps: parseInt(options.inputSteps),
        gruUnits: parseInt(options.gruUnits),
        epochs: parseInt(options.epochs),
        confidenceThreshold: parseFloat(options.threshold),
        symbol: options.symbol,
        mode: options.mode as 'live' | 'backtest',
      });
    });

  program.parse(process.argv);

  // Run main if no command specified
  if (!process.argv.slice(2).length) {
    main();
    program.help();
  }
}
