-- Migration: Tenant Error Tracking
-- Tables: tenant_error_entries, tenant_error_rules

CREATE TABLE IF NOT EXISTS tenant_error_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  error_type TEXT NOT NULL,
  message TEXT NOT NULL,
  stack_trace TEXT,
  endpoint TEXT,
  status_code INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_error_entries_tenant ON tenant_error_entries(tenant_id);

CREATE TABLE IF NOT EXISTS tenant_error_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  error_pattern TEXT NOT NULL,
  action TEXT NOT NULL DEFAULT 'alert',
  notification_channel TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_error_rules_tenant ON tenant_error_rules(tenant_id);
