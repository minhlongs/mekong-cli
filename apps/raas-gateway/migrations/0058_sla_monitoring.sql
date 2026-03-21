-- Migration 0058: SLA Monitoring + Uptime Tracking
-- Creates uptime_checks and sla_breaches tables

CREATE TABLE IF NOT EXISTS uptime_checks (
  id TEXT PRIMARY KEY,
  check_type TEXT NOT NULL DEFAULT 'api',
  status TEXT NOT NULL,
  latency_ms INTEGER NOT NULL,
  details TEXT,
  checked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_uptime_checks_time ON uptime_checks(checked_at);
CREATE INDEX IF NOT EXISTS idx_uptime_checks_status ON uptime_checks(status, checked_at);

CREATE TABLE IF NOT EXISTS sla_breaches (
  id TEXT PRIMARY KEY,
  breach_type TEXT NOT NULL,
  target_value REAL NOT NULL,
  actual_value REAL NOT NULL,
  tier TEXT NOT NULL,
  started_at TEXT NOT NULL,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sla_breaches_time ON sla_breaches(created_at);
