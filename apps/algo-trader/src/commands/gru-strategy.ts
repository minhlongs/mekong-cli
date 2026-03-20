/**
 * GRU Strategy CLI Command
 *
 * Run GRU neural network trading strategy live or in backtest mode.
 */

import { GruStrategy } from '../strategies/GruStrategy';
import { DataPreprocessor, OhlcvData } from '../ml/gru/data-preprocessor';

export interface GruCommandOptions {
  inputSteps: number;
  gruUnits: number;
  epochs: number;
  confidenceThreshold: number;
  symbol: string;
  interval: string;
  mode: 'live' | 'backtest';
}

export async function runGruStrategy(options: Partial<GruCommandOptions> = {}): Promise<void> {
  const config: GruCommandOptions = {
    inputSteps: options.inputSteps || 60,
    gruUnits: options.gruUnits || 64,
    epochs: options.epochs || 50,
    confidenceThreshold: options.confidenceThreshold || 0.7,
    symbol: options.symbol || 'BTC/USDT',
    interval: options.interval || '1h',
    mode: options.mode || 'backtest',
  };

  console.log('='.repeat(60));
  console.log('  GRU Neural Network Trading Strategy');
  console.log('='.repeat(60));
  console.log(`Symbol: ${config.symbol}`);
  console.log(`Interval: ${config.interval}`);
  console.log(`Mode: ${config.mode.toUpperCase()}`);
  console.log(`Input Steps: ${config.inputSteps}`);
  console.log(`GRU Units: ${config.gruUnits}`);
  console.log(`Epochs: ${config.epochs}`);
  console.log(`Confidence Threshold: ${(config.confidenceThreshold * 100).toFixed(0)}%`);
  console.log('='.repeat(60));

  try {
    // Initialize strategy
    const strategy = new GruStrategy({
      inputSteps: config.inputSteps,
      gruUnits: config.gruUnits,
      epochs: config.epochs,
      confidenceThreshold: config.confidenceThreshold,
    });

    console.log('\n[1/3] Initializing GRU model...');
    await strategy.initialize();

    // Generate mock historical data for demo
    console.log('\n[2/3] Loading historical data...');
    const historicalData = generateMockData(config.inputSteps + 20);
    console.log(`Loaded ${historicalData.length} candles`);

    // Train model
    console.log('\n[3/3] Training GRU model...');
    await strategy.train(historicalData);

    console.log('\n' + '='.repeat(60));
    console.log('  Training Complete - Ready for Trading');
    console.log('='.repeat(60));

    // Run live or backtest
    if (config.mode === 'live') {
      console.log('\n🔴 LIVE TRADING MODE - Simulated');
      console.log('Watching for new candles...\n');

      // Simulate a few trading cycles
      for (let i = 0; i < 5; i++) {
        const newCandle = generateMockCandle(historicalData[historicalData.length - 1]);
        const signal = await strategy.execute([newCandle]);

        console.log(`\n[${new Date().toISOString()}] ${config.symbol}`);
        console.log(`  Price: $${newCandle.close.toFixed(2)}`);
        console.log(`  Signal: ${signal.action.toUpperCase()}`);
        console.log(`  Confidence: ${(signal.confidence * 100).toFixed(1)}%`);
        console.log(`  Reason: ${signal.reason}`);

        await sleep(1000);
      }
    } else {
      console.log('\n📊 BACKTEST MODE');
      console.log('Running on historical data...\n');

      let wins = 0;
      let losses = 0;

      for (let i = 20; i < historicalData.length; i++) {
        const inputCandles = historicalData.slice(i - config.inputSteps, i);
        const nextCandle = historicalData[i];

        const signal = await strategy.execute(inputCandles);

        if (signal.action !== 'wait') {
          const predictedUp = signal.action === 'buy';
          const actualUp = nextCandle.close > inputCandles[inputCandles.length - 1].close;

          if (predictedUp === actualUp) {
            wins++;
            console.log(`✓ Candle ${i}: ${signal.action.toUpperCase()} - Correct!`);
          } else {
            losses++;
            console.log(`✗ Candle ${i}: ${signal.action.toUpperCase()} - Wrong`);
          }
        }
      }

      console.log('\n' + '='.repeat(60));
      console.log('  Backtest Results');
      console.log('='.repeat(60));
      console.log(`Wins: ${wins}`);
      console.log(`Losses: ${losses}`);
      console.log(`Win Rate: ${((wins / (wins + losses)) * 100).toFixed(1)}%`);
    }

    // Cleanup
    strategy.dispose?.();

    console.log('\n✅ GRU Strategy session complete.\n');
  } catch (error) {
    console.error('\n❌ Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

// Helper functions
function generateMockData(count: number): OhlcvData[] {
  const data: OhlcvData[] = [];
  let price = 50000; // Starting BTC price

  for (let i = 0; i < count; i++) {
    const change = (Math.random() - 0.48) * 1000; // Slight upward bias
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 200;
    const low = Math.min(open, close) - Math.random() * 200;
    const volume = Math.random() * 10000 + 5000;

    data.push({
      timestamp: Date.now() - (count - i) * 3600000,
      open,
      high,
      low,
      close,
      volume,
    });

    price = close;
  }

  return data;
}

function generateMockCandle(prev: OhlcvData): OhlcvData {
  const change = (Math.random() - 0.48) * 500;
  const open = prev.close;
  const close = open + change;

  return {
    timestamp: Date.now(),
    open,
    high: Math.max(open, close) + Math.random() * 100,
    low: Math.min(open, close) - Math.random() * 100,
    close,
    volume: Math.random() * 10000 + 5000,
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
