-- Migration 0053: Multi-Currency Billing Support
-- Adds exchange_rates and tenant_currency_prefs tables

CREATE TABLE IF NOT EXISTS exchange_rates (
  id TEXT PRIMARY KEY,
  from_currency TEXT NOT NULL,
  to_currency TEXT NOT NULL,
  rate REAL NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(from_currency, to_currency)
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair ON exchange_rates(from_currency, to_currency);

CREATE TABLE IF NOT EXISTS tenant_currency_prefs (
  tenant_id TEXT PRIMARY KEY,
  preferred_currency TEXT NOT NULL DEFAULT 'USD',
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
