-- Migration 0223: Tenant Data Export
-- Tables for managing tenant data export requests and schemas

CREATE TABLE IF NOT EXISTS data_export_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  export_type TEXT NOT NULL DEFAULT 'full',
  format TEXT NOT NULL DEFAULT 'json',
  status TEXT NOT NULL DEFAULT 'pending',
  file_url TEXT,
  requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  expires_at TEXT
);
CREATE INDEX idx_data_export_requests_tenant ON data_export_requests(tenant_id);

CREATE TABLE IF NOT EXISTS data_export_schemas (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  schema_name TEXT NOT NULL,
  tables_included TEXT,
  fields_excluded TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_data_export_schemas_tenant ON data_export_schemas(tenant_id);
