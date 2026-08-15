import { describe, it, expect } from 'vitest';
import { sha256, shortId, generateId } from '../../src/utils/hash.js';
import { parseDuration, validateNonEmpty, validateRange } from '../../src/utils/validation.js';

describe('hash utils', () => {
  it('sha256 produces consistent hash', () => {
    expect(sha256('hello')).toBe(sha256('hello'));
    expect(sha256('hello')).not.toBe(sha256('world'));
  });

  it('shortId is 8 chars', () => {
    expect(shortId('test')).toHaveLength(8);
  });

  it('generateId creates unique ids', () => {
    const id1 = generateId();
    const id2 = generateId();
    expect(id1).not.toBe(id2);
  });

  it('generateId with prefix', () => {
    const id = generateId('task');
    expect(id).toMatch(/^task_/);
  });
});

describe('validation utils', () => {
  it('parseDuration handles seconds', () => {
    const result = parseDuration('5s');
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toBe(5000);
  });

  it('parseDuration handles minutes', () => {
    const result = parseDuration('30m');
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toBe(1800000);
  });

  it('parseDuration rejects invalid', () => {
    const result = parseDuration('abc');
    expect(result.ok).toBe(false);
  });

  it('validateNonEmpty rejects empty', () => {
    const result = validateNonEmpty('', 'name');
    expect(result.ok).toBe(false);
  });

  it('validateNonEmpty accepts valid', () => {
    const result = validateNonEmpty('hello', 'name');
    expect(result.ok).toBe(true);
  });

  it('validateRange checks bounds', () => {
    expect(validateRange(5, 1, 10, 'x').ok).toBe(true);
    expect(validateRange(0, 1, 10, 'x').ok).toBe(false);
    expect(validateRange(11, 1, 10, 'x').ok).toBe(false);
  });
});
