-- Migration 0081: Adaptive Rate Limiting V2 — Tenant-aware quotas with tier defaults

CREATE TABLE IF NOT EXISTS rate_limit_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  requests_per_minute INTEGER DEFAULT 60,
  requests_per_hour INTEGER DEFAULT 1000,
  burst_allowance INTEGER DEFAULT 10,
  throttle_strategy TEXT DEFAULT 'sliding_window',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id, endpoint_pattern)
);

CREATE TABLE IF NOT EXISTS rate_limit_violations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  violation_type TEXT NOT NULL,
  request_count INTEGER,
  limit_value INTEGER,
  occurred_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tier_rate_defaults (
  id TEXT PRIMARY KEY,
  tier TEXT NOT NULL UNIQUE,
  requests_per_minute INTEGER DEFAULT 60,
  requests_per_hour INTEGER DEFAULT 1000,
  daily_limit INTEGER DEFAULT 10000,
  burst_allowance INTEGER DEFAULT 10,
  concurrent_limit INTEGER DEFAULT 5
);

CREATE INDEX IF NOT EXISTS idx_rl_configs_tenant ON rate_limit_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rl_violations_tenant ON rate_limit_violations(tenant_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_tier_defaults ON tier_rate_defaults(tier);
