-- Migration 0238: Tenant API Gateway Logs
-- Tracks per-tenant API request logs and configurable log filters

CREATE TABLE IF NOT EXISTS api_gateway_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  request_id TEXT,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_gateway_logs_tenant ON api_gateway_logs(tenant_id);

CREATE TABLE IF NOT EXISTS api_gateway_log_filters (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  filter_name TEXT NOT NULL,
  path_pattern TEXT,
  min_status INTEGER,
  max_status INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_gateway_log_filters_tenant ON api_gateway_log_filters(tenant_id);
