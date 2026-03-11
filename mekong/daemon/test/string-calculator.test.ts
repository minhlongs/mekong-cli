
import { describe, it, expect } from 'vitest';
import { add } from '../src/string-calculator';

describe('String Calculator', () => {
  it('should return 0 for an empty string', () => {
    expect(add('')).toBe(0);
  });
});
