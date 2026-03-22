-- Migration: Tenant API Rate Policies
-- Stores per-tenant, per-endpoint rate limit policy configurations and violation logs

CREATE TABLE IF NOT EXISTS api_rate_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  requests_per_minute INTEGER NOT NULL DEFAULT 60,
  burst_size INTEGER NOT NULL DEFAULT 10,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_rate_policies_tenant ON api_rate_policies(tenant_id);

CREATE TABLE IF NOT EXISTS api_rate_policy_violations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  violated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  request_count INTEGER,
  endpoint TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_rate_policy_violations_tenant ON api_rate_policy_violations(tenant_id);
