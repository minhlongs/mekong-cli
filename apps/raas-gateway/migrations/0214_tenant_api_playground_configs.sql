-- Migration 0214: Tenant API Playground Configs
-- Saved API playground configurations and execution history per tenant

CREATE TABLE IF NOT EXISTS playground_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'GET',
  headers_json TEXT NOT NULL DEFAULT '{}',
  body_json TEXT,
  is_shared INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playground_executions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  response_status INTEGER,
  response_time_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_playground_configs_tenant_id
  ON playground_configs (tenant_id);

CREATE INDEX IF NOT EXISTS idx_playground_executions_tenant_id
  ON playground_executions (tenant_id);

CREATE INDEX IF NOT EXISTS idx_playground_executions_config_id
  ON playground_executions (config_id);
