-- Migration: Tenant API Health Monitor
-- Tracks per-tenant external endpoint health checks and results

CREATE TABLE IF NOT EXISTS api_health_monitors (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  monitor_name TEXT NOT NULL,
  endpoint_url TEXT NOT NULL,
  check_interval_ms INTEGER NOT NULL DEFAULT 60000,
  expected_status INTEGER DEFAULT 200,
  status TEXT NOT NULL DEFAULT 'active',
  last_checked_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_health_monitors_tenant ON api_health_monitors(tenant_id);

CREATE TABLE IF NOT EXISTS api_health_monitor_results (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  monitor_id TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  healthy INTEGER NOT NULL DEFAULT 1,
  checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_health_monitor_results_monitor ON api_health_monitor_results(monitor_id);
