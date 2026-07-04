/**
 * Minimal logger for arbitrage modules — wraps console.
 * Consumers can override via setLogger() to use winston/pino/etc.
 */

export interface ArbLogger {
  info(msg: string): void;
  warn(msg: string): void;
  error(msg: string): void;
}

const consoleLogger: ArbLogger = {
  info: (msg: string) => console.log(`[arb] ${msg}`),
  warn: (msg: string) => console.warn(`[arb] ${msg}`),
  error: (msg: string) => console.error(`[arb] ${msg}`),
};

let activeLogger: ArbLogger = consoleLogger;

export function getArbLogger(): ArbLogger {
  return activeLogger;
}

export function setArbLogger(logger: ArbLogger): void {
  activeLogger = logger;
}
