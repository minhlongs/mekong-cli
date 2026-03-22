-- Tenant API Access Control
-- Tables: api_access_rules, api_access_audit

CREATE TABLE IF NOT EXISTS api_access_rules (
  id                TEXT PRIMARY KEY,
  tenant_id         TEXT NOT NULL,
  resource_pattern  TEXT NOT NULL,
  action            TEXT NOT NULL DEFAULT 'allow',
  conditions_json   TEXT NOT NULL DEFAULT '{}',
  priority          INTEGER NOT NULL DEFAULT 0,
  is_active         INTEGER NOT NULL DEFAULT 1,
  created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_access_rules_tenant_id ON api_access_rules (tenant_id);

CREATE TABLE IF NOT EXISTS api_access_audit (
  id            TEXT PRIMARY KEY,
  tenant_id     TEXT NOT NULL,
  rule_id       TEXT,
  request_path  TEXT NOT NULL,
  action_taken  TEXT NOT NULL,
  ip_address    TEXT,
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_access_audit_tenant_id ON api_access_audit (tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_access_audit_rule_id   ON api_access_audit (rule_id);
