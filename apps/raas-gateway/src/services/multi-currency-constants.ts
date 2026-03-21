/**
 * Multi-Currency constants — rates, tier prices, currency metadata
 */

import type { CurrencyInfo, Currency } from './multi-currency-service';

// Default exchange rates (USD base)
export const DEFAULT_RATES: Record<Currency, number> = {
  USD: 1,
  EUR: 0.92,
  GBP: 0.79,
  VND: 25400,
  JPY: 155,
  SGD: 1.35,
};

// Tier prices in USD
export const TIER_PRICES: Record<string, number> = {
  starter: 49,
  pro: 149,
  agency: 299,
  master: 499,
  enterprise: 999,
};

export const CURRENCY_INFO: CurrencyInfo[] = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'VND', symbol: '₫', name: 'Vietnamese Dong' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar' },
];
