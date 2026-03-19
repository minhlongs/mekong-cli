export * from './types.js';
export * from './locales/index.js';
// Hooks and other exports will be added as they are implemented

/** Configurable logger for i18n scripts */
const DEBUG = typeof process !== 'undefined'
  ? process.env.NODE_ENV === 'development'
  : true;

export const logger = {
  info: (msg: string, meta?: Record<string, unknown>): void => {
    if (DEBUG) console.log(`[INFO] ${msg}`, meta ?? '');
  },
  debug: (msg: string, meta?: Record<string, unknown>): void => {
    if (DEBUG) console.debug(`[DEBUG] ${msg}`, meta ?? '');
  },
  warn: (msg: string, meta?: Record<string, unknown>): void => {
    console.warn(`[WARN] ${msg}`, meta ?? '');
  },
  error: (msg: string, meta?: Record<string, unknown>): void => {
    console.error(`[ERROR] ${msg}`, meta ?? '');
  },
};
