/**
 * ARB:AUTO Command - Autonomous Arbitrage Trading
 * Full autonomous trading loop with WS feeds, spread detection, atomic execution
 */

import { TradingLoop } from '../arbitrage/trading-loop';
import { existsSync } from 'fs';
import { join } from 'path';

const ENV_PATH = join(process.cwd(), '.env');

export interface AutoCommandOptions {
  symbols?: string;
  exchanges?: string;
  minSpread?: number;
  dryRun?: boolean;
  verbose?: boolean;
}

export async function runArbAuto(options: AutoCommandOptions = {}): Promise<void> {
  console.log('\n⚡ ARB:AUTO — Autonomous Arbitrage Trading\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Check configuration
  if (!existsSync(ENV_PATH)) {
    console.log('⚠️  No .env found. Please run `algo-trader setup` first.\n');
    console.log('Or create .env with:\n');
    console.log('  EXCHANGE_API_KEY=your_api_key');
    console.log('  EXCHANGE_SECRET=your_secret');
    console.log('  REDIS_URL=redis://localhost:6379');
    console.log('  DATABASE_URL=postgresql://...\n');
    process.exit(1);
  }

  // Parse options
  const symbols = options.symbols
    ? options.symbols.split(',').map((s) => s.trim())
    : ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'];

  const exchanges = options.exchanges
    ? options.exchanges.split(',').map((e) => e.trim().toLowerCase())
    : ['binance', 'okx', 'bybit'];

  const minSpread = options.minSpread || 0.05;
  const dryRun = options.dryRun ?? true;
  const verbose = options.verbose ?? true;

  console.log('📋 Configuration:');
  console.log(`  Symbols: ${symbols.join(', ')}`);
  console.log(`  Exchanges: ${exchanges.join(', ')}`);
  console.log(`  Min Spread: ${minSpread}%`);
  console.log(`  Mode: ${dryRun ? 'DRY-RUN' : 'LIVE'}`);
  console.log(`  Verbose: ${verbose ? 'Yes' : 'No'}\n`);

  if (dryRun) {
    console.log('📝 DRY-RUN MODE — No real trades will be executed\n');
  } else {
    console.log('⚠️  LIVE MODE — Real money at risk!\n');
    const confirm = await promptConfirmation();
    if (!confirm) {
      console.log('\n⚠️  Live trading cancelled. Exiting.\n');
      process.exit(0);
    }
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Initialize trading loop
  const tradingLoop = new TradingLoop({
    symbols,
    exchanges: exchanges as ('binance' | 'okx' | 'bybit')[],
    minSpreadPercent: minSpread,
    enableDryRun: dryRun,
    enableLogging: verbose,
    checkIntervalMs: 100,
  });

  // Setup event handlers
  tradingLoop.on('started', (data) => {
    console.log(`\n✅ Trading loop started`);
    console.log(`   Symbols: ${data.symbols.length}`);
    console.log(`   Exchanges: ${data.exchanges.length}\n`);
  });

  tradingLoop.on('opportunity', (opp) => {
    console.log(`\n🎯 OPPORTUNITY DETECTED`);
    console.log(`   ID: ${opp.id}`);
    console.log(`   Symbol: ${opp.symbol}`);
    console.log(`   Buy: ${opp.buyExchange} @ $${opp.buyPrice}`);
    console.log(`   Sell: ${opp.sellExchange} @ $${opp.sellPrice}`);
    console.log(`   Spread: ${opp.spreadPercent.toFixed(4)}%`);
    console.log(`   Score: ${opp.score || 'N/A'}`);
    console.log(`   Confidence: ${opp.confidence || 'N/A'}\n`);
  });

  tradingLoop.on('execution', ({ opportunity, result }) => {
    if (result.success) {
      console.log(`\n✅ EXECUTION SUCCESS`);
      console.log(`   Opportunity: ${opportunity.id}`);
      console.log(`   Profit: $${result.actualProfit.toFixed(2)} (${result.actualProfitPct.toFixed(4)}%)\n`);
    } else {
      console.log(`\n❌ EXECUTION FAILED`);
      console.log(`   Opportunity: ${opportunity.id}`);
      console.log(`   Error: ${result.error}\n`);
    }
  });

  tradingLoop.on('stopped', (metrics) => {
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📊 TRADING LOOP STOPPED');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`   Uptime: ${metrics.uptimeMs}ms`);
    console.log(`   Opportunities: ${metrics.opportunitiesFound}`);
    console.log(`   Executed: ${metrics.opportunitiesExecuted}`);
    console.log(`   Total Profit: $${metrics.totalProfit.toFixed(2)}`);
    console.log(`   Avg Latency: ${metrics.avgLatencyMs}ms`);
    console.log(`   P95 Latency: ${metrics.p95LatencyMs}ms`);
    console.log(`   Errors: ${metrics.errors}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  });

  // Handle graceful shutdown
  const shutdown = async () => {
    console.log('\n\n🛑 Shutdown requested...\n');
    await tradingLoop.stop();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  // Start trading loop
  try {
    await tradingLoop.start();

    console.log('🔍 Scanning markets for arbitrage opportunities...\n');
    console.log('Press Ctrl+C to stop\n');

    // Print metrics periodically
    setInterval(() => {
      const metrics = tradingLoop.getMetrics();
      if (metrics.isRunning) {
        console.log(`\n📈 METRICS: Opps=${metrics.opportunitiesFound} Exec=${metrics.opportunitiesExecuted} P95=${metrics.p95LatencyMs}ms Profit=$${metrics.totalProfit.toFixed(2)}\n`);
      }
    }, 60000); // Every minute

  } catch (error) {
    console.error('\n❌ TRADING LOOP ERROR\n');
    console.error(error instanceof Error ? error.message : String(error));
    console.error('\nPlease check your configuration and try again.\n');
    await tradingLoop.stop();
    process.exit(1);
  }
}

async function promptConfirmation(): Promise<boolean> {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    readline.question('Confirm live trading with real money? (y/N): ', (answer: string) => {
      readline.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
    });
  });
}
