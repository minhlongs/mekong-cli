import chalk from 'chalk';
import type { Logger } from '../types/index.js';

export interface LoggerOptions {
  verbose?: boolean;
  prefix?: string;
  silent?: boolean;
}

/**
 * Create a logger instance with configurable options
 */
export function createLogger(options: LoggerOptions = {}): Logger {
  const { verbose = false, prefix = '[mekong]', silent = false } = options;
  
  return {
    debug: (msg: string, meta?: Record<string, unknown>) => {
      if (silent) return;
      if (verbose) {
        console.log(chalk.gray(`${prefix} ${msg}`), meta ? stringifyMeta(meta) : '');
      }
    },
    
    info: (msg: string, meta?: Record<string, unknown>) => {
      if (silent) return;
      console.log(chalk.blue(`${prefix} ${msg}`), meta ? stringifyMeta(meta) : '');
    },
    
    warn: (msg: string, meta?: Record<string, unknown>) => {
      if (silent) return;
      console.warn(chalk.yellow(`${prefix} ⚠ ${msg}`), meta ? stringifyMeta(meta) : '');
    },
    
    error: (msg: string, meta?: Record<string, unknown>) => {
      if (silent) return;
      console.error(chalk.red(`${prefix} ✖ ${msg}`), meta ? stringifyMeta(meta) : '');
    },
  };
}

/**
 * Create a silent logger (for testing)
 */
export function createSilentLogger(): Logger {
  return createLogger({ silent: true });
}

/**
 * Stringify metadata for logging
 */
function stringifyMeta(meta: Record<string, unknown>): string {
  try {
    return JSON.stringify(meta);
  } catch {
    return '[Circular]';
  }
}
