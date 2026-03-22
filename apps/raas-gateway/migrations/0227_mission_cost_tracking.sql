-- Migration 0227: Mission Cost Tracking
-- Tracks execution costs per mission with tenant budget management

CREATE TABLE IF NOT EXISTS mission_costs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  cost_type TEXT NOT NULL DEFAULT 'compute',
  amount REAL NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'USD',
  provider TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_costs_tenant ON mission_costs(tenant_id);

CREATE TABLE IF NOT EXISTS mission_cost_budgets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  budget_name TEXT NOT NULL,
  monthly_limit REAL NOT NULL,
  current_spend REAL NOT NULL DEFAULT 0,
  alert_threshold REAL NOT NULL DEFAULT 0.8,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_cost_budgets_tenant ON mission_cost_budgets(tenant_id);
