CREATE TABLE IF NOT EXISTS mission_sla_policies (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, policy_name TEXT NOT NULL,
  max_execution_time_ms INTEGER NOT NULL DEFAULT 30000,
  min_success_rate REAL NOT NULL DEFAULT 0.95, evaluation_window TEXT DEFAULT '24h',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mission_sla_policies_tenant ON mission_sla_policies(tenant_id);

CREATE TABLE IF NOT EXISTS mission_sla_violations (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, policy_id TEXT NOT NULL,
  mission_id TEXT, violation_type TEXT NOT NULL, details_json TEXT DEFAULT '{}',
  resolved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mission_sla_violations_tenant ON mission_sla_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_sla_violations_policy ON mission_sla_violations(policy_id);
