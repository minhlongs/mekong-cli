-- Migration 0232: Tenant API Versioning Config
-- Stores per-tenant API versioning configuration and version mappings

CREATE TABLE IF NOT EXISTS api_versioning_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  api_version TEXT NOT NULL DEFAULT 'v1',
  deprecation_policy TEXT,
  sunset_date TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_versioning_configs_tenant ON api_versioning_configs(tenant_id);

CREATE TABLE IF NOT EXISTS api_version_mappings (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  old_version TEXT NOT NULL,
  new_version TEXT NOT NULL,
  redirect_enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_version_mappings_tenant ON api_version_mappings(tenant_id);
