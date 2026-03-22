-- Tenant API rate burst — token-bucket configs and per-request events
CREATE TABLE IF NOT EXISTS rate_burst_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  bucket_size INTEGER DEFAULT 100,
  refill_rate INTEGER DEFAULT 10,
  refill_interval_ms INTEGER DEFAULT 1000,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rate_burst_configs_tenant_id ON rate_burst_configs(tenant_id);

-- Per-request burst events for audit and analytics
CREATE TABLE IF NOT EXISTS rate_burst_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  tokens_remaining INTEGER NOT NULL,
  was_throttled INTEGER DEFAULT 0,
  request_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rate_burst_events_tenant_id ON rate_burst_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rate_burst_events_config_id ON rate_burst_events(config_id);
