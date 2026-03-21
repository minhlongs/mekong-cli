/**
 * Multi-Currency Service — exchange rates, conversion, tenant preferences
 */

import { DEFAULT_RATES, TIER_PRICES, CURRENCY_INFO } from './multi-currency-constants';

export type Currency = 'USD' | 'EUR' | 'VND' | 'GBP' | 'JPY' | 'SGD';

export interface ExchangeRate {
  from: Currency;
  to: Currency;
  rate: number;
  updated_at: string;
}

export interface ConvertResult {
  amount: number;
  rate: number;
  from: Currency;
  to: Currency;
}

export interface CurrencyInfo {
  code: Currency;
  symbol: string;
  name: string;
}

/**
 * Convert amount between currencies using stored or default rates
 */
export async function convertAmount(
  amount: number,
  from: Currency,
  to: Currency,
  db?: D1Database
): Promise<ConvertResult> {
  if (from === to) return { amount, rate: 1, from, to };

  let rate: number | null = null;

  // Try stored rate first
  if (db) {
    try {
      const row = await db
        .prepare('SELECT rate FROM exchange_rates WHERE from_currency = ? AND to_currency = ?')
        .bind(from, to)
        .first<{ rate: number }>();
      if (row) rate = row.rate;
    } catch {
      // Fall through to default
    }
  }

  // Fall back to default rates (convert via USD base)
  if (rate === null) {
    const fromUsd = DEFAULT_RATES[from] ?? 1;
    const toUsd = DEFAULT_RATES[to] ?? 1;
    rate = toUsd / fromUsd;
  }

  return { amount: Math.round(amount * rate * 100) / 100, rate, from, to };
}

/**
 * Fetch all stored exchange rates ordered by most recent
 */
export async function getExchangeRates(db: D1Database): Promise<ExchangeRate[]> {
  const result = await db
    .prepare('SELECT from_currency, to_currency, rate, updated_at FROM exchange_rates ORDER BY updated_at DESC')
    .all<{ from_currency: string; to_currency: string; rate: number; updated_at: string }>();

  return (result.results ?? []).map((r) => ({
    from: r.from_currency as Currency,
    to: r.to_currency as Currency,
    rate: r.rate,
    updated_at: r.updated_at,
  }));
}

/**
 * Upsert exchange rate for a currency pair
 */
export async function updateExchangeRate(
  db: D1Database,
  from: Currency,
  to: Currency,
  rate: number
): Promise<{ success: boolean; rate: number }> {
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO exchange_rates (id, from_currency, to_currency, rate, updated_at)
       VALUES (?, ?, ?, ?, datetime('now'))
       ON CONFLICT(from_currency, to_currency) DO UPDATE SET rate = excluded.rate, updated_at = excluded.updated_at`
    )
    .bind(id, from, to, rate)
    .run();
  return { success: true, rate };
}

/**
 * Get tenant's preferred currency (defaults to USD)
 */
export async function getTenantCurrency(db: D1Database, tenantId: string): Promise<Currency> {
  try {
    const row = await db
      .prepare('SELECT preferred_currency FROM tenant_currency_prefs WHERE tenant_id = ?')
      .bind(tenantId)
      .first<{ preferred_currency: string }>();
    return (row?.preferred_currency as Currency) ?? 'USD';
  } catch {
    return 'USD';
  }
}

/**
 * Upsert tenant's preferred currency
 */
export async function setTenantCurrency(
  db: D1Database,
  tenantId: string,
  currency: Currency
): Promise<{ success: boolean }> {
  await db
    .prepare(
      `INSERT INTO tenant_currency_prefs (tenant_id, preferred_currency, updated_at)
       VALUES (?, ?, datetime('now'))
       ON CONFLICT(tenant_id) DO UPDATE SET preferred_currency = excluded.preferred_currency, updated_at = excluded.updated_at`
    )
    .bind(tenantId, currency)
    .run();
  return { success: true };
}

/**
 * Get all tier pricing converted to target currency
 */
export async function getPricingInCurrency(
  currency: Currency,
  db?: D1Database
): Promise<Record<string, { usd: number; converted: number; currency: Currency }>> {
  const pricing: Record<string, { usd: number; converted: number; currency: Currency }> = {};
  for (const [tier, usdPrice] of Object.entries(TIER_PRICES)) {
    const result = await convertAmount(usdPrice, 'USD', currency, db);
    pricing[tier] = { usd: usdPrice, converted: result.amount, currency };
  }
  return pricing;
}

/**
 * Get invoice with amounts converted to tenant's preferred currency
 */
export async function getInvoiceInCurrency(
  db: D1Database,
  tenantId: string,
  invoiceId: string
): Promise<Record<string, unknown> | null> {
  const invoice = await db
    .prepare('SELECT * FROM invoices WHERE id = ? AND tenant_id = ?')
    .bind(invoiceId, tenantId)
    .first<Record<string, unknown>>();

  if (!invoice) return null;

  const currency = await getTenantCurrency(db, tenantId);
  const usdAmount = typeof invoice.amount === 'number' ? invoice.amount : 0;
  const converted = await convertAmount(usdAmount, 'USD', currency, db);

  return { ...invoice, converted_amount: converted.amount, display_currency: currency };
}

/**
 * List all supported currencies with symbols and names
 */
export function getSupportedCurrencies(): CurrencyInfo[] {
  return CURRENCY_INFO;
}
