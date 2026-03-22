-- Migration 0126: Tenant API Key Management
-- Tables: api_keys, api_key_usage_logs

CREATE TABLE IF NOT EXISTS api_keys (
  id            TEXT PRIMARY KEY,
  tenant_id     TEXT NOT NULL,
  name          TEXT NOT NULL,
  key_hash      TEXT NOT NULL,
  key_prefix    TEXT NOT NULL,
  scopes_json   TEXT DEFAULT '["read"]',
  status        TEXT DEFAULT 'active',
  expires_at    TEXT,
  last_used_at  TEXT,
  usage_count   INTEGER DEFAULT 0,
  created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
  revoked_at    TEXT
);

CREATE TABLE IF NOT EXISTS api_key_usage_logs (
  id          TEXT PRIMARY KEY,
  api_key_id  TEXT NOT NULL,
  endpoint    TEXT NOT NULL,
  method      TEXT NOT NULL,
  status_code INTEGER,
  ip_address  TEXT,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id  ON api_keys (tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash   ON api_keys (key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_prefix ON api_keys (key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_status     ON api_keys (status);

-- Indexes for api_key_usage_logs
CREATE INDEX IF NOT EXISTS idx_api_key_usage_logs_api_key_id ON api_key_usage_logs (api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_logs_created_at ON api_key_usage_logs (created_at);
