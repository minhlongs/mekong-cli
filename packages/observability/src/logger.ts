/**
 * Structured logger for Mekong CLI.
 * Supports debug/info/warn/error levels with JSON output.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  module?: string;
  event?: string;
  data?: unknown;
  error?: Error;
}

export interface LoggerConfig {
  minLevel: LogLevel;
  format: 'json' | 'pretty';
  output: (entry: LogEntry) => void;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

/** Default console output */
function defaultOutput(entry: LogEntry): void {
  if (entry.level === 'error') {
    console.error(formatEntry(entry));
  } else if (entry.level === 'warn') {
    console.warn(formatEntry(entry));
  } else {
    console.log(formatEntry(entry));
  }
}

function formatEntry(entry: LogEntry): string {
  const json = JSON.stringify({
    level: entry.level,
    message: entry.message,
    timestamp: entry.timestamp,
    module: entry.module,
    event: entry.event,
    data: entry.data,
    error: entry.error?.stack || entry.error?.message,
  });
  return json;
}

/** Default configuration */
const DEFAULT_CONFIG: LoggerConfig = {
  minLevel: 'info',
  format: 'json',
  output: defaultOutput,
};

export class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.minLevel];
  }

  private createEntry(level: LogLevel, message: string, meta?: Record<string, unknown>): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...meta,
    };
  }

  debug(message: string, meta?: Record<string, unknown>): void {
    if (!this.shouldLog('debug')) return;
    const entry = this.createEntry('debug', message, meta);
    this.config.output(entry);
  }

  info(message: string, meta?: Record<string, unknown>): void {
    if (!this.shouldLog('info')) return;
    const entry = this.createEntry('info', message, meta);
    this.config.output(entry);
  }

  warn(message: string, meta?: Record<string, unknown>): void {
    if (!this.shouldLog('warn')) return;
    const entry = this.createEntry('warn', message, meta);
    this.config.output(entry);
  }

  error(message: string, error?: Error, meta?: Record<string, unknown>): void {
    if (!this.shouldLog('error')) return;
    const entry = this.createEntry('error', message, { ...meta, error });
    this.config.output(entry);
  }

  child(module: string): Logger {
    return new Logger({
      ...this.config,
      output: (entry) => {
        entry.module = module;
        this.config.output(entry);
      },
    });
  }
}

/** Global logger instance */
export const logger = new Logger();

/** Set global log level - creates new logger instance */
export function setLogLevel(level: LogLevel): Logger {
  return new Logger({ minLevel: level });
}
