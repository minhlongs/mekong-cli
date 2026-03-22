-- Migration: Tenant Integration Connectors
-- Stores per-tenant connector configurations and sync event logs

CREATE TABLE IF NOT EXISTS integration_connectors (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  connector_name TEXT NOT NULL,
  connector_type TEXT NOT NULL,
  config_json TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  last_sync_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_integration_connectors_tenant ON integration_connectors(tenant_id);

CREATE TABLE IF NOT EXISTS integration_connector_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  connector_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  details TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_integration_connector_logs_tenant ON integration_connector_logs(tenant_id);
