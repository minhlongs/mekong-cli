-- Migration 0114: API Rate Limit Policies
-- Tables: rate_limit_policies, rate_limit_policy_templates, rate_limit_violations

CREATE TABLE IF NOT EXISTS rate_limit_policies (
  id TEXT PRIMARY KEY DEFAULT ('rlp_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL, -- e.g. '/v1/missions/*'
  method TEXT DEFAULT '*', -- GET, POST, *, etc
  max_requests INTEGER NOT NULL DEFAULT 100,
  window_seconds INTEGER NOT NULL DEFAULT 60,
  burst_limit INTEGER DEFAULT 0,
  action_on_limit TEXT NOT NULL DEFAULT 'reject', -- reject, queue, throttle
  is_active INTEGER NOT NULL DEFAULT 1,
  priority INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rlp_tenant ON rate_limit_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rlp_endpoint ON rate_limit_policies(endpoint_pattern, method);

CREATE TABLE IF NOT EXISTS rate_limit_policy_templates (
  id TEXT PRIMARY KEY DEFAULT ('rlt_' || lower(hex(randomblob(8)))),
  template_name TEXT NOT NULL UNIQUE,
  description TEXT,
  policies_json TEXT NOT NULL, -- JSON array of policy configs
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rate_limit_violations (
  id TEXT PRIMARY KEY DEFAULT ('rlv_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  violation_count INTEGER NOT NULL DEFAULT 1,
  window_start TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rlv_tenant ON rate_limit_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rlv_policy ON rate_limit_violations(policy_id);
