-- Migration 0235: Tenant data retention policies and execution log
-- Tracks per-tenant retention rules and audit of past executions

CREATE TABLE IF NOT EXISTS data_retention_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  data_type TEXT NOT NULL,
  retention_days INTEGER NOT NULL DEFAULT 365,
  action TEXT NOT NULL DEFAULT 'archive',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_retention_policies_tenant ON data_retention_policies(tenant_id);

CREATE TABLE IF NOT EXISTS data_retention_executions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  records_processed INTEGER DEFAULT 0,
  records_deleted INTEGER DEFAULT 0,
  executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_retention_executions_tenant ON data_retention_executions(tenant_id);
