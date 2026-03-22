-- Migration: Tenant API Gateway Logs
CREATE TABLE IF NOT EXISTS api_gateway_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  response_time_ms INTEGER,
  request_size INTEGER DEFAULT 0,
  response_size INTEGER DEFAULT 0,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_gateway_logs_tenant ON api_gateway_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_gateway_logs_created ON api_gateway_logs(created_at);

CREATE TABLE IF NOT EXISTS api_gateway_log_summaries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  total_requests INTEGER NOT NULL DEFAULT 0,
  avg_response_time_ms REAL DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  top_paths_json TEXT DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_gateway_log_summaries_tenant ON api_gateway_log_summaries(tenant_id);
