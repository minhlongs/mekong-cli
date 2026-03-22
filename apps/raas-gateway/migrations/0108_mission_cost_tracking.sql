-- Migration 0108: Mission Cost Tracking
-- Tracks per-mission LLM costs, compute time, and credit usage with tenant budget management

CREATE TABLE IF NOT EXISTS mission_costs (
  id TEXT PRIMARY KEY DEFAULT ('mc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  model_provider TEXT, -- anthropic, openai, google, dashscope
  model_name TEXT,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0, -- in USD
  compute_time_ms INTEGER NOT NULL DEFAULT 0,
  credit_cost REAL NOT NULL DEFAULT 0, -- in MCU credits
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_mcost_tenant ON mission_costs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mcost_mission ON mission_costs(mission_id);
CREATE INDEX IF NOT EXISTS idx_mcost_created ON mission_costs(tenant_id, created_at);

CREATE TABLE IF NOT EXISTS cost_budgets (
  id TEXT PRIMARY KEY DEFAULT ('cb_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL UNIQUE,
  monthly_budget_usd REAL,
  daily_budget_usd REAL,
  alert_threshold_pct REAL DEFAULT 80, -- alert at 80% of budget
  current_month_spend REAL NOT NULL DEFAULT 0,
  current_day_spend REAL NOT NULL DEFAULT 0,
  last_reset_date TEXT,
  is_hard_limit INTEGER NOT NULL DEFAULT 0, -- block missions when exceeded
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cb_tenant ON cost_budgets(tenant_id);
