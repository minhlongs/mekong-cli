-- Migration: Tenant API Throttling
-- Tables for per-tenant endpoint throttle rules and throttle event logs

CREATE TABLE IF NOT EXISTS throttle_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  requests_per_minute INTEGER NOT NULL DEFAULT 60,
  burst_limit INTEGER NOT NULL DEFAULT 10,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_throttle_rules_tenant_id ON throttle_rules (tenant_id);

CREATE TABLE IF NOT EXISTS throttle_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  request_path TEXT NOT NULL,
  client_ip TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_throttle_events_tenant_id ON throttle_events (tenant_id);
