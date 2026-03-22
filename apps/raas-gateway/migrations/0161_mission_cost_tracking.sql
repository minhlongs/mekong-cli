-- Wave 62: Mission Cost Tracking
-- Tables: mission_costs, cost_budgets

CREATE TABLE IF NOT EXISTS mission_costs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  cost_type TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT DEFAULT 'USD',
  provider TEXT,
  model TEXT,
  tokens_used INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_budgets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  monthly_limit REAL NOT NULL,
  current_spend REAL DEFAULT 0,
  alert_threshold REAL DEFAULT 0.8,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped and mission-scoped queries
CREATE INDEX IF NOT EXISTS idx_mission_costs_tenant_id ON mission_costs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_costs_mission_id ON mission_costs(mission_id);
CREATE INDEX IF NOT EXISTS idx_cost_budgets_tenant_id ON cost_budgets(tenant_id);
