// Main entry point - export all public APIs
export * from './types/index.js';
export * from './config/index.js';
export { createLogger, createSilentLogger, type LoggerOptions } from './utils/logger.js';
export {
  BuildOptimizerError,
  ConfigError,
  BuildError,
  AgentError,
  OptimizationFailedError,
  ValidationError,
} from './utils/errors.js';
export { readJson, writeJson, ensureDir, fileExists, ensureParentDir } from './utils/fs.js';

// Package version
export const VERSION = '0.1.0';
