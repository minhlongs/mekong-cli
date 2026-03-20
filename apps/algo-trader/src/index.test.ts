import { describe, it, expect } from 'vitest';
import { version, main } from './index';

describe('Algo Trader', () => {
  it('should have correct version', () => {
    expect(version).toBe('1.0.0');
  });

  it('should run main without errors', () => {
    expect(() => main()).not.toThrow();
  });
});
