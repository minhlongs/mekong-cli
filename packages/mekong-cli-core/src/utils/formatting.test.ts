import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  formatPercentage,
  formatNumber,
  formatCompactNumber,
} from './formatting';

describe('formatCurrency', () => {
  it('should format USD currency', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency(-500)).toBe('-$500.00');
  });

  it('should format VND currency', () => {
    expect(formatCurrency(1000000, { currency: 'VND' })).toBe('₫1,000,000.00');
  });

  it('should format EUR currency', () => {
    expect(formatCurrency(999.99, { currency: 'EUR' })).toBe('€999.99');
  });

  it('should handle custom decimal places', () => {
    expect(formatCurrency(100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })).toBe('$100');
    expect(formatCurrency(100.555, { minimumFractionDigits: 3, maximumFractionDigits: 3 })).toBe('$100.555');
  });

  it('should handle large numbers', () => {
    expect(formatCurrency(1000000.99)).toBe('$1,000,000.99');
    expect(formatCurrency(9999999999.99)).toBe('$9,999,999,999.99');
  });

  it('should throw error for non-finite numbers', () => {
    expect(() => formatCurrency(NaN)).toThrow('Invalid amount');
    expect(() => formatCurrency(Infinity)).toThrow('Invalid amount');
    expect(() => formatCurrency(-Infinity)).toThrow('Invalid amount');
  });
});

describe('formatPercentage', () => {
  it('should format percentage values', () => {
    expect(formatPercentage(0.5)).toBe('50.0%');
    expect(formatPercentage(1)).toBe('100.0%');
    expect(formatPercentage(0)).toBe('0.0%');
  });

  it('should handle decimal precision', () => {
    expect(formatPercentage(0.333, { minimumFractionDigits: 2, maximumFractionDigits: 2 })).toBe('33.30%');
    expect(formatPercentage(0.9999, { minimumFractionDigits: 3, maximumFractionDigits: 3 })).toBe('99.990%');
  });

  it('should handle negative percentages', () => {
    expect(formatPercentage(-0.1)).toBe('-10.0%');
  });

  it('should format as decimal when style is decimal', () => {
    expect(formatPercentage(0.75, { style: 'decimal' })).toBe('75.0%');
  });

  it('should throw error for non-finite numbers', () => {
    expect(() => formatPercentage(NaN)).toThrow('Invalid value');
    expect(() => formatPercentage(Infinity)).toThrow('Invalid value');
    expect(() => formatPercentage(-Infinity)).toThrow('Invalid value');
  });

  it('should handle values greater than 1', () => {
    expect(formatPercentage(1.5)).toBe('150.0%');
    expect(formatPercentage(2)).toBe('200.0%');
  });
});

describe('formatNumber', () => {
  it('should format numbers with grouping', () => {
    expect(formatNumber(1234567)).toBe('1,234,567');
    expect(formatNumber(1000)).toBe('1,000');
  });

  it('should format decimals', () => {
    expect(formatNumber(1234.567)).toBe('1,234.57');
    expect(formatNumber(0.1)).toBe('0.1');
  });

  it('should handle custom precision', () => {
    expect(formatNumber(100, { minimumFractionDigits: 2, maximumFractionDigits: 2 })).toBe('100.00');
    expect(formatNumber(100.999, { minimumFractionDigits: 0, maximumFractionDigits: 0 })).toBe('101');
  });

  it('should disable grouping when requested', () => {
    expect(formatNumber(10000, { useGrouping: false })).toBe('10000');
  });

  it('should throw error for non-finite numbers', () => {
    expect(() => formatNumber(NaN)).toThrow('Invalid value');
    expect(() => formatNumber(Infinity)).toThrow('Invalid value');
    expect(() => formatNumber(-Infinity)).toThrow('Invalid value');
  });
});

describe('formatCompactNumber', () => {
  it('should format thousands with K suffix', () => {
    expect(formatCompactNumber(1500)).toBe('1.5K');
    expect(formatCompactNumber(2000)).toBe('2K');
  });

  it('should format millions with M suffix', () => {
    expect(formatCompactNumber(1500000)).toBe('1.5M');
    expect(formatCompactNumber(2000000)).toBe('2M');
  });

  it('should format billions with B suffix', () => {
    expect(formatCompactNumber(1500000000)).toBe('1.5B');
  });

  it('should handle custom precision', () => {
    expect(formatCompactNumber(1234, { precision: 2 })).toBe('1.23K');
    expect(formatCompactNumber(1234567, { precision: 3 })).toBe('1.235M');
  });

  it('should throw error for non-finite numbers', () => {
    expect(() => formatCompactNumber(NaN)).toThrow('Invalid value');
    expect(() => formatCompactNumber(Infinity)).toThrow('Invalid value');
    expect(() => formatCompactNumber(-Infinity)).toThrow('Invalid value');
  });

  it('should handle negative numbers', () => {
    expect(formatCompactNumber(-1500)).toBe('-1.5K');
    expect(formatCompactNumber(-2000000)).toBe('-2M');
  });
});
