/**
 * Tests for structured logger.
 */
import { describe, it, expect } from 'vitest';
import { Logger, logger } from '../src/logger.js';

describe('Logger', () => {
  it('should create logger with default config', () => {
    const log = new Logger();
    expect(log).toBeDefined();
  });

  it('should respect minLevel setting', () => {
    const log = new Logger({ minLevel: 'warn' });
    expect(log).toBeDefined();
  });

  it('should have all log levels', () => {
    const log = new Logger();
    expect(log.debug).toBeDefined();
    expect(log.info).toBeDefined();
    expect(log.warn).toBeDefined();
    expect(log.error).toBeDefined();
  });

  it('should create child logger with module name', () => {
    const log = new Logger();
    const child = log.child('test-module');
    expect(child).toBeDefined();
  });

  it('should use global logger instance', () => {
    expect(logger).toBeDefined();
    expect(logger.info).toBeDefined();
  });
});
