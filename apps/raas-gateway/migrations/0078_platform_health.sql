-- Migration 0078: Platform Health Dashboard tables
CREATE TABLE IF NOT EXISTS platform_health_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_type TEXT NOT NULL,
  metrics TEXT NOT NULL DEFAULT '{}',
  score REAL DEFAULT 100.0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS service_status (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL UNIQUE,
  status TEXT DEFAULT 'operational',
  last_check_at TEXT,
  response_time_ms INTEGER,
  error_message TEXT,
  metadata TEXT DEFAULT '{}'
);

CREATE INDEX idx_health_snapshots_type ON platform_health_snapshots(snapshot_type, created_at);
CREATE INDEX idx_service_status_name ON service_status(service_name);
