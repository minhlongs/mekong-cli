/**
 * Formatting utilities for currency, percentages, and numbers
 */

export interface CurrencyOptions {
  currency?: 'USD' | 'VND' | 'EUR' | 'GBP';
  locale?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
}

export interface PercentageOptions {
  locale?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  style?: 'decimal' | 'percent';
}

export interface NumberOptions {
  locale?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  useGrouping?: boolean;
}

const DEFAULT_CURRENCY_OPTIONS: Required<CurrencyOptions> = {
  currency: 'USD',
  locale: 'en-US',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
};

const DEFAULT_PERCENTAGE_OPTIONS: Required<PercentageOptions> = {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
  style: 'percent',
};

const DEFAULT_NUMBER_OPTIONS: Required<NumberOptions> = {
  locale: 'en-US',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
  useGrouping: true,
};

/**
 * Format a number as currency
 * @param amount - The amount to format
 * @param options - Currency formatting options
 * @returns Formatted currency string
 * @throws Error if amount is not a finite number
 */
export function formatCurrency(
  amount: number,
  options: CurrencyOptions = {}
): string {
  if (!Number.isFinite(amount)) {
    throw new Error(`Invalid amount: expected finite number, got ${amount}`);
  }

  const opts = { ...DEFAULT_CURRENCY_OPTIONS, ...options };

  return new Intl.NumberFormat(opts.locale, {
    style: 'currency',
    currency: opts.currency,
    minimumFractionDigits: opts.minimumFractionDigits,
    maximumFractionDigits: opts.maximumFractionDigits,
  }).format(amount);
}

/**
 * Format a number as percentage
 * @param value - The value to format (0.5 = 50%)
 * @param options - Percentage formatting options
 * @returns Formatted percentage string
 * @throws Error if value is not a finite number
 */
export function formatPercentage(
  value: number,
  options: PercentageOptions = {}
): string {
  if (!Number.isFinite(value)) {
    throw new Error(`Invalid value: expected finite number, got ${value}`);
  }

  const opts = { ...DEFAULT_PERCENTAGE_OPTIONS, ...options };

  if (opts.style === 'percent') {
    return new Intl.NumberFormat(opts.locale === 'auto' ? undefined : opts.locale, {
      style: 'percent',
      minimumFractionDigits: opts.minimumFractionDigits,
      maximumFractionDigits: opts.maximumFractionDigits,
    }).format(value);
  }

  // Decimal style (e.g., "50.00%" instead of "50.00 %")
  const decimalValue = value * 100;
  return new Intl.NumberFormat(opts.locale === 'auto' ? undefined : opts.locale, {
    minimumFractionDigits: opts.minimumFractionDigits,
    maximumFractionDigits: opts.maximumFractionDigits,
  }).format(decimalValue) + '%';
}

/**
 * Format a number with grouping and decimal places
 * @param value - The number to format
 * @param options - Number formatting options
 * @returns Formatted number string
 * @throws Error if value is not a finite number
 */
export function formatNumber(
  value: number,
  options: NumberOptions = {}
): string {
  if (!Number.isFinite(value)) {
    throw new Error(`Invalid value: expected finite number, got ${value}`);
  }

  const opts = { ...DEFAULT_NUMBER_OPTIONS, ...options };

  return new Intl.NumberFormat(opts.locale, {
    minimumFractionDigits: opts.minimumFractionDigits,
    maximumFractionDigits: opts.maximumFractionDigits,
    useGrouping: opts.useGrouping,
  }).format(value);
}

/**
 * Format large numbers with K/M/B suffixes
 * @param value - The number to format
 * @param options - Formatting options
 * @returns Formatted number with suffix
 * @throws Error if value is not a finite number
 */
export function formatCompactNumber(
  value: number,
  options: { locale?: string; precision?: number } = {}
): string {
  if (!Number.isFinite(value)) {
    throw new Error(`Invalid value: expected finite number, got ${value}`);
  }

  const { locale = 'en-US', precision = 1 } = options;

  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: precision,
  }).format(value);
}
