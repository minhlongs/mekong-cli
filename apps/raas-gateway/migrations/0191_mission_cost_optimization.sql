CREATE TABLE IF NOT EXISTS cost_optimization_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  condition_json TEXT NOT NULL DEFAULT '{}',
  action_type TEXT NOT NULL DEFAULT 'downgrade_model',
  savings_estimate REAL NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cost_optimization_rules_tenant ON cost_optimization_rules(tenant_id);

CREATE TABLE IF NOT EXISTS cost_optimization_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  original_cost REAL NOT NULL,
  optimized_cost REAL NOT NULL,
  savings REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cost_optimization_events_tenant ON cost_optimization_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cost_optimization_events_rule ON cost_optimization_events(rule_id);
