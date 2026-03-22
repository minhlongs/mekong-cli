-- Tenant API Usage Analytics — detailed per-request tracking and period summaries

CREATE TABLE IF NOT EXISTS api_usage_analytics (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  request_size INTEGER,
  response_size INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_analytics_tenant ON api_usage_analytics(tenant_id);

CREATE TABLE IF NOT EXISTS api_usage_summaries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  total_requests INTEGER NOT NULL DEFAULT 0,
  avg_response_time_ms REAL,
  error_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_summaries_tenant ON api_usage_summaries(tenant_id);
