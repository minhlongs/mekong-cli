-- Tenant API Schema Validation: rules + violation tracking
CREATE TABLE IF NOT EXISTS api_schema_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  schema_json TEXT NOT NULL,
  validation_mode TEXT NOT NULL DEFAULT 'warn',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_schema_rules_tenant ON api_schema_rules(tenant_id);

CREATE TABLE IF NOT EXISTS api_schema_violations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  request_path TEXT NOT NULL,
  violation_details TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'warning',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_schema_violations_tenant ON api_schema_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_schema_violations_rule ON api_schema_violations(rule_id);
