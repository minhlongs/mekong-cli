-- Tenant API throttling rules and events
-- Controls max concurrent requests per endpoint pattern per tenant

CREATE TABLE IF NOT EXISTS api_throttle_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  max_concurrent INTEGER NOT NULL DEFAULT 10,
  queue_timeout_ms INTEGER NOT NULL DEFAULT 30000,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_throttle_rules_tenant ON api_throttle_rules(tenant_id);

CREATE TABLE IF NOT EXISTS api_throttle_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  event_type TEXT NOT NULL DEFAULT 'throttled',
  request_path TEXT,
  queued_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_throttle_events_tenant ON api_throttle_events(tenant_id);
