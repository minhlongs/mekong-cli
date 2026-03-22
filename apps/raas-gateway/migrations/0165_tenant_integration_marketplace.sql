-- Migration: Tenant Integration Marketplace
-- Tables for managing tenant integrations and their audit logs

CREATE TABLE IF NOT EXISTS integrations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  integration_type TEXT NOT NULL,
  provider_name TEXT NOT NULL,
  config_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active',
  last_sync_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integrations_tenant_id ON integrations (tenant_id);

CREATE TABLE IF NOT EXISTS integration_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  integration_id TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  details TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integration_logs_tenant_id ON integration_logs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_integration_logs_integration_id ON integration_logs (integration_id);
