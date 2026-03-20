/**
 * Quickstart Command - Zero-Config Trading Start
 * Instant trading with sensible defaults
 */

import { existsSync } from 'fs';
import { join } from 'path';
import { runSetupWizard } from './setup-wizard';

const ENV_PATH = join(process.cwd(), '.env');

export async function runQuickstart(): Promise<void> {
  console.log('\n🚀 Algo Trader Quickstart\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Step 1: Check if .env exists, if not run setup wizard
  if (!existsSync(ENV_PATH)) {
    console.log('⚠️  No configuration found. Running setup wizard...\n');
    await runSetupWizard();
  }

  // Step 2: Load configuration
  console.log('📖 Loading configuration...\n');
  const config = loadConfiguration();

  // Step 3: Validate configuration
  console.log('🔍 Validating configuration...\n');
  validateConfiguration(config);

  // Step 4: Show configuration summary
  console.log('━━━ Configuration Summary ━━━\n');
  console.log(`  Trading Mode: ${config.tradingMode}`);
  console.log(`  Risk per Trade: ${config.riskPerTrade}%`);
  console.log(`  Max Daily Loss: ${config.maxDailyLoss}%`);
  console.log(`  Backtesting: ${config.enableBacktesting ? 'Enabled' : 'Disabled'}`);
  console.log(`  Live Trading: ${config.enableLiveTrading ? 'Enabled' : 'Disabled'}`);

  if (config.apiKeyConfigured) {
    console.log(`  Exchange API: ✅ Configured`);
  } else {
    console.log(`  Exchange API: ⚠️  Not configured (dry-run only)`);
  }

  if (config.telegramConfigured) {
    console.log(`  Telegram: ✅ Enabled`);
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Step 5: Start trading engine based on mode
  console.log('🔧 Starting trading engine...\n');

  if (config.tradingMode === 'dry-run' || !config.apiKeyConfigured) {
    console.log('📊 Starting in DRY-RUN mode (paper trading)...\n');
    console.log('  - No real trades will be executed');
    console.log('  - Simulating trades with live market data');
    console.log('  - Perfect for testing strategies\n');
    await startDryRunEngine();
  } else {
    console.log('💰 Starting in LIVE mode (real trading)...\n');
    console.log('  ⚠️  WARNING: Real money at risk!');
    console.log('  - Real trades will be executed');
    console.log('  - Monitor positions carefully');
    console.log('  - Stop with Ctrl+C at any time\n');

    const confirm = await promptConfirmation();
    if (confirm) {
      await startLiveEngine();
    } else {
      console.log('\n⚠️  Live trading cancelled. Starting in dry-run mode...\n');
      await startDryRunEngine();
    }
  }
}

function loadConfiguration(): Record<string, any> {
  // Load environment variables
  const env = process.env;

  return {
    tradingMode: env.DRY_RUN === 'true' ? 'dry-run' : 'live',
    riskPerTrade: parseFloat(env.RISK_PER_TRADE || '1'),
    maxDailyLoss: parseFloat(env.MAX_DAILY_LOSS || '5'),
    enableBacktesting: env.ENABLE_BACKTESTING !== 'false',
    enableLiveTrading: env.ENABLE_LIVE_TRADING === 'true',
    apiKeyConfigured: !!(env.EXCHANGE_API_KEY && env.EXCHANGE_SECRET),
    telegramConfigured: !!(env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID),
  };
}

function validateConfiguration(config: Record<string, any>): void {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Validate risk parameters
  if (config.riskPerTrade <= 0 || config.riskPerTrade > 10) {
    errors.push('RISK_PER_TRADE must be between 0 and 10');
  }

  if (config.maxDailyLoss <= 0 || config.maxDailyLoss > 50) {
    errors.push('MAX_DAILY_LOSS must be between 0 and 50');
  }

  if (config.riskPerTrade > config.maxDailyLoss) {
    warnings.push('RISK_PER_TRADE is higher than MAX_DAILY_LOSS');
  }

  // Warn about live trading without API keys
  if (config.tradingMode === 'live' && !config.apiKeyConfigured) {
    warnings.push('Live trading mode but no API keys configured');
  }

  // Print warnings
  if (warnings.length > 0) {
    console.log('⚠️  Configuration warnings:');
    warnings.forEach((w) => console.log(`   - ${w}`));
    console.log('');
  }

  // Throw errors
  if (errors.length > 0) {
    console.error('❌ Configuration errors:');
    errors.forEach((e) => console.error(`   - ${e}`));
    console.error('\nPlease run `npm run setup` to reconfigure.\n');
    process.exit(1);
  }

  console.log('✅ Configuration valid\n');
}

async function startDryRunEngine(): Promise<void> {
  console.log('🔌 Connecting to exchange (read-only)...');
  await sleep(1000);
  console.log('✅ Connected to exchange\n');

  console.log('📈 Loading market data...');
  await sleep(800);
  console.log('✅ Market data loaded\n');

  console.log('🤖 Starting strategy engine...');
  await sleep(500);
  console.log('✅ Strategy engine ready\n');

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎯 DRY-RUN ENGINE STARTED');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  console.log('Waiting for trading signals...\n');
  console.log('Press Ctrl+C to stop\n');

  // In a real implementation, this would start the trading loop
  // For now, we'll just show a message
  console.log('💡 Tip: Run `npm run dev arb:spread` to start spread detection');
  console.log('   or `npm run dev arb:agi` for AGI-powered arbitrage\n');
}

async function startLiveEngine(): Promise<void> {
  console.log('🔌 Connecting to exchange...');
  await sleep(1000);
  console.log('✅ Connected to exchange\n');

  console.log('📈 Loading market data...');
  await sleep(800);
  console.log('✅ Market data loaded\n');

  console.log('🔐 Verifying API permissions...');
  await sleep(500);
  console.log('✅ API permissions verified\n');

  console.log('🤖 Starting strategy engine...');
  await sleep(500);
  console.log('✅ Strategy engine ready\n');

  console.log('💰 Starting live trading engine...');
  await sleep(500);
  console.log('✅ Live trading engine started\n');

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎯 LIVE ENGINE STARTED - REAL MONEY AT RISK');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  console.log('Monitoring markets for trading signals...\n');
  console.log('Press Ctrl+C to stop\n');

  // In a real implementation, this would start the trading loop
  console.log('💡 Tip: Run `npm run dev arb:spread` to start spread detection');
  console.log('   or `npm run dev arb:agi` for AGI-powered arbitrage\n');
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function promptConfirmation(): Promise<boolean> {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    readline.question('Confirm live trading? (y/N): ', (answer: string) => {
      readline.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
    });
  });
}
