-- Migration: Platform cost dashboard — cost entries and budget tracking
-- Tracks platform-level spending by category/provider with monthly budget alerts

CREATE TABLE IF NOT EXISTS platform_cost_entries (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  provider TEXT NOT NULL,
  service_name TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  period TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platform_cost_budgets (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  monthly_budget REAL NOT NULL,
  alert_threshold REAL NOT NULL DEFAULT 0.8,
  current_spend REAL NOT NULL DEFAULT 0,
  period TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for category-scoped queries
CREATE INDEX IF NOT EXISTS idx_platform_cost_entries_category
  ON platform_cost_entries (category);

CREATE INDEX IF NOT EXISTS idx_platform_cost_entries_period
  ON platform_cost_entries (period);

CREATE INDEX IF NOT EXISTS idx_platform_cost_budgets_category
  ON platform_cost_budgets (category);

CREATE INDEX IF NOT EXISTS idx_platform_cost_budgets_period
  ON platform_cost_budgets (period);
