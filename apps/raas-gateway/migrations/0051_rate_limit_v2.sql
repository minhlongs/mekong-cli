-- Migration: Rate Limit V2 — Token Bucket custom configs + event log
-- Wave 24.1

CREATE TABLE IF NOT EXISTS rate_limit_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  requests_per_minute INTEGER NOT NULL,
  burst_allowance INTEGER NOT NULL,
  cooldown_seconds INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rate_limit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_events_tenant ON rate_limit_events(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rate_limit_events_time ON rate_limit_events(created_at);
