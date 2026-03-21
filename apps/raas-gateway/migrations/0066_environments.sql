-- Migration 0066: Environment Management
-- Adds per-tenant environments (staging/production) with variable support

CREATE TABLE IF NOT EXISTS environments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  env_type TEXT NOT NULL CHECK(env_type IN ('production','staging','development','testing')),
  description TEXT,
  config TEXT DEFAULT '{}', -- JSON: custom env config
  api_base_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_environments_tenant ON environments(tenant_id);
CREATE UNIQUE INDEX idx_environments_tenant_name ON environments(tenant_id, name);

CREATE TABLE IF NOT EXISTS environment_variables (
  id TEXT PRIMARY KEY,
  environment_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  is_secret BOOLEAN DEFAULT FALSE,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_env_vars_env ON environment_variables(environment_id);
CREATE UNIQUE INDEX idx_env_vars_env_key ON environment_variables(environment_id, key);
