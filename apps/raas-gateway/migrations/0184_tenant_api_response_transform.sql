CREATE TABLE IF NOT EXISTS api_response_transforms (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, rule_name TEXT NOT NULL,
  match_pattern TEXT NOT NULL, transform_type TEXT NOT NULL DEFAULT 'map',
  transform_config_json TEXT DEFAULT '{}', priority INTEGER DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_response_transforms_tenant ON api_response_transforms(tenant_id);

CREATE TABLE IF NOT EXISTS api_response_transform_logs (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, transform_id TEXT NOT NULL,
  request_path TEXT, applied INTEGER NOT NULL DEFAULT 1,
  execution_time_ms INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_response_transform_logs_tenant ON api_response_transform_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_response_transform_logs_transform ON api_response_transform_logs(transform_id);
