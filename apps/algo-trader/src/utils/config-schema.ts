/**
 * Zod validation schemas for algo-trader configuration.
 * Validates environment variables at startup to catch misconfiguration early.
 */

import { z } from 'zod';
import { BOT_ENGINE, RISK_MANAGEMENT } from './constants';

export const ExchangeCredentialsSchema = z.object({
  EXCHANGE_API_KEY: z.string().min(10, 'API key must be at least 10 chars'),
  EXCHANGE_SECRET: z.string().min(10, 'API secret must be at least 10 chars'),
});

export const TradingConfigSchema = z.object({
  EXCHANGE_ID: z.string().min(1).default('binance'),
  TRADING_PAIR: z.string().regex(/^[A-Z0-9]+\/[A-Z0-9]+$/, 'Must be format BASE/QUOTE').default('BTC/USDT'),
  TIMEFRAME: z.enum(['1m', '5m', '15m', '1h', '4h', '1d']).default('1h'),
  RSI_PERIOD: z.coerce.number().int().positive().default(14),
  SMA_SHORT: z.coerce.number().int().positive().default(9),
  SMA_LONG: z.coerce.number().int().positive().default(21),
  MAX_POSITION_SIZE: z.coerce.number().positive().max(1, 'Must be 0-1 fraction').default(0.1),
  STOP_LOSS_PCT: z.coerce.number().positive().max(100).default(2),
  TAKE_PROFIT_PCT: z.coerce.number().positive().max(100).default(4),
  MAX_DAILY_LOSS: z.coerce.number().positive().max(100).default(5),
});

/**
 * Bot Engine Configuration Schema with validation guards
 * Phase 18: Safety & Resilience — Config Validation Layer
 */
export const BotEngineConfigSchema = z.object({
  tenantId: z.string().min(1, 'tenantId is required'),
  symbol: z.string().regex(/^[A-Z0-9]+\/[A-Z0-9]+$/, 'symbol must be format BASE/QUOTE (e.g., BTC/USDT)'),
  riskPercentage: z.coerce.number()
    .gt(0, 'riskPercentage must be greater than 0')
    .lte(1, 'riskPercentage must be at most 1 (100%)'),
  pollInterval: z.coerce.number()
    .gte(BOT_ENGINE.MIN_POLL_INTERVAL_MS, `pollInterval must be at least ${BOT_ENGINE.MIN_POLL_INTERVAL_MS}ms`)
    .lte(BOT_ENGINE.MAX_POLL_INTERVAL_MS, `pollInterval must be at most ${BOT_ENGINE.MAX_POLL_INTERVAL_MS}ms`),
  maxDrawdownPercent: z.coerce.number()
    .gt(0, 'maxDrawdownPercent must be greater than 0')
    .lte(RISK_MANAGEMENT.MAX_DRAWDOWN_HARD_LIMIT, `maxDrawdownPercent cannot exceed ${RISK_MANAGEMENT.MAX_DRAWDOWN_HARD_LIMIT}%`)
    .optional(),
  minPositionValueUsd: z.coerce.number().positive().default(BOT_ENGINE.MIN_POSITION_VALUE_USD),
  feeRate: z.coerce.number().positive().lte(0.1).default(BOT_ENGINE.DEFAULT_FEE_RATE),
  stopLoss: z.object({
    percentage: z.coerce.number().positive().max(100),
    trailing: z.boolean().default(false),
  }).optional(),
  autonomyLevel: z.enum(['FULL_AUTO', 'ACT_CONFIRM', 'MANUAL']).default('ACT_CONFIRM'),
});

export const LogConfigSchema = z.object({
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'http', 'verbose', 'debug', 'silly']).default('info'),
  LOG_FILE: z.string().optional(),
});

export const AppConfigSchema = z.object({
  ...ExchangeCredentialsSchema.shape,
  ...TradingConfigSchema.shape,
  ...LogConfigSchema.shape,
});

export type AppConfig = z.infer<typeof AppConfigSchema>;
export type BotEngineConfig = z.infer<typeof BotEngineConfigSchema>;

/**
 * Parse and validate process.env against AppConfigSchema.
 * Throws ZodError with human-readable messages on failure.
 */
export function validateConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  const result = AppConfigSchema.safeParse(env);
  if (!result.success) {
    const issues = result.error.issues
      .map(i => `  ${i.path.join('.')}: ${i.message}`)
      .join('\n');
    throw new Error(`Config validation failed:\n${issues}`);
  }
  return result.data;
}

/**
 * Validate Bot Engine configuration object.
 * Used for validating BotConfig before bot startup.
 * Phase 18: Safety & Resilience — Config Validation Layer
 */
export function validateBotEngineConfig(config: unknown): BotEngineConfig {
  const result = BotEngineConfigSchema.safeParse(config);
  if (!result.success) {
    const issues = result.error.issues
      .map(i => `  ${i.path.join('.')}: ${i.message}`)
      .join('\n');
    throw new Error(`Bot Engine config validation failed:\n${issues}`);
  }
  return result.data;
}
