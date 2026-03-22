-- Migration: Tenant API Rate Quotas
CREATE TABLE IF NOT EXISTS api_rate_quotas (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  max_requests_per_minute INTEGER NOT NULL DEFAULT 60,
  max_requests_per_hour INTEGER NOT NULL DEFAULT 1000,
  max_requests_per_day INTEGER NOT NULL DEFAULT 10000,
  burst_limit INTEGER DEFAULT 100,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_rate_quotas_tenant ON api_rate_quotas(tenant_id);

CREATE TABLE IF NOT EXISTS api_rate_quota_usage (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  quota_id TEXT NOT NULL,
  period TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  blocked_count INTEGER NOT NULL DEFAULT 0,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_rate_quota_usage_tenant ON api_rate_quota_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_rate_quota_usage_quota ON api_rate_quota_usage(quota_id);
