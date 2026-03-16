/**
 * Trading Constants — Centralized magic numbers for maintainability.
 * Phase 18: Safety & Resilience
 */

/**
 * Technical Analysis Defaults
 */
export const TECHNICAL_ANALYSIS = {
  // RSI (Relative Strength Index)
  RSI_PERIOD: 14,
  RSI_OVERBOUGHT: 70,
  RSI_OVERSOLD: 30,

  // SMA (Simple Moving Average)
  SMA_SHORT_PERIOD: 9,
  SMA_LONG_PERIOD: 21,

  // Bollinger Bands
  BOLLINGER_PERIOD: 20,
  BOLLINGER_STD_DEV: 2,

  // MACD
  MACD_FAST: 12,
  MACD_SLOW: 26,
  MACD_SIGNAL: 9,

  // ATR (Average True Range)
  ATR_PERIOD: 14,
} as const;

/**
 * Risk Management Defaults
 */
export const RISK_MANAGEMENT = {
  // Position Sizing
  DEFAULT_RISK_PERCENTAGE: 0.1, // 10% of balance per trade
  MAX_POSITION_SIZE: 1, // 100% of balance

  // Stop Loss & Take Profit
  DEFAULT_STOP_LOSS_PCT: 2, // 2%
  DEFAULT_TAKE_PROFIT_PCT: 4, // 4%
  DEFAULT_TRAILING_STOP_PCT: 0.02, // 2%

  // Drawdown Protection
  DEFAULT_MAX_DRAWDOWN_PERCENT: 10, // 10% max drawdown
  MAX_DRAWDOWN_HARD_LIMIT: 20, // 20% hard circuit breaker

  // Daily Loss Limits
  DEFAULT_DAILY_LOSS_LIMIT: 5, // 5% of portfolio
  DAILY_LOSS_HARD_LIMIT: 10, // 10% hard limit

  // Consecutive Loss Limits
  MAX_CONSECUTIVE_LOSSES: 5,

  // Volatility Sizing
  VOLATILITY_RISK_PERCENT: 2,
  ATR_THRESHOLD_HIGH: 3,
  ATR_THRESHOLD_ELEVATED: 2,
} as const;

/**
 * Bot Engine Defaults
 */
export const BOT_ENGINE = {
  // Polling
  DEFAULT_POLL_INTERVAL_MS: 5000, // 5 seconds
  MIN_POLL_INTERVAL_MS: 1000, // 1 second minimum
  MAX_POLL_INTERVAL_MS: 60000, // 1 minute maximum

  // Position Tracking
  MIN_POSITION_VALUE_USD: 10, // Minimum USD value to consider position open

  // Trading Fees
  DEFAULT_FEE_RATE: 0.001, // 0.1% per side

  // Retry & Recovery
  MAX_CONSECUTIVE_ERRORS: 5,
  RETRY_DELAY_MS: 1000,
} as const;

/**
 * Backtest Defaults
 */
export const BACKTEST = {
  // Slippage & Commission
  DEFAULT_SLIPPAGE_PCT: 0.05, // 0.05%
  DEFAULT_COMMISSION_PCT: 0.1, // 0.1%

  // Initial Capital
  DEFAULT_INITIAL_CAPITAL: 10000, // $10,000
} as const;

/**
 * Alert & Notification Defaults
 */
export const ALERTS = {
  // Rate Limiting
  TELEGRAM_RATE_LIMIT_MS: 1000, // 1 second between messages

  // Alert Thresholds
  PNL_ALERT_THRESHOLD_USD: 100, // Alert on PnL > $100
  DRAWDOWN_ALERT_THRESHOLD_PCT: 5, // Alert on 5% drawdown
} as const;

/**
 * Timeframe Options
 */
export const TIMEFRAMES = [
  '1m',
  '5m',
  '15m',
  '1h',
  '4h',
  '1d',
] as const;

/**
 * Exchange Defaults
 */
export const EXCHANGE = {
  DEFAULT_EXCHANGE_ID: 'binance',
  TRADING_PAIR_FORMAT: /^[A-Z0-9]+\/[A-Z0-9]+$/,
} as const;

/**
 * Log Levels
 */
export const LOG_LEVELS = [
  'error',
  'warn',
  'info',
  'http',
  'verbose',
  'debug',
  'silly',
] as const;
