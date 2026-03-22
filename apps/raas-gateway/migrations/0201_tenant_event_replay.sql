-- Migration: Tenant event replay configuration and run tracking
-- Allows tenants to configure source event types, target endpoints, and replay speed

CREATE TABLE IF NOT EXISTS event_replay_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  source_event_type TEXT NOT NULL,
  target_endpoint TEXT NOT NULL,
  filter_json TEXT NOT NULL DEFAULT '{}',
  replay_speed REAL NOT NULL DEFAULT 1.0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_replay_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  events_replayed INTEGER NOT NULL DEFAULT 0,
  events_failed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_event_replay_configs_tenant_id
  ON event_replay_configs (tenant_id);

CREATE INDEX IF NOT EXISTS idx_event_replay_runs_tenant_id
  ON event_replay_runs (tenant_id);

CREATE INDEX IF NOT EXISTS idx_event_replay_runs_config_id
  ON event_replay_runs (config_id);
