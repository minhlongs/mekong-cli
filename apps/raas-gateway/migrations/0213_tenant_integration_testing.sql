-- Migration: Tenant integration testing — configs and results tracking
-- Supports per-tenant endpoint testing with scheduling and admin overview

CREATE TABLE IF NOT EXISTS integration_test_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  test_name TEXT NOT NULL,
  target_endpoint TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'GET',
  expected_status INTEGER NOT NULL DEFAULT 200,
  headers_json TEXT NOT NULL DEFAULT '{}',
  body_json TEXT,
  schedule_cron TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integration_test_results (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pass',
  response_status INTEGER,
  response_time_ms INTEGER,
  error_message TEXT,
  executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_integration_test_configs_tenant_id
  ON integration_test_configs (tenant_id);

CREATE INDEX IF NOT EXISTS idx_integration_test_results_tenant_id
  ON integration_test_results (tenant_id);

CREATE INDEX IF NOT EXISTS idx_integration_test_results_config_id
  ON integration_test_results (config_id);
