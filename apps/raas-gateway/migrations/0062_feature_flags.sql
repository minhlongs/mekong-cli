-- Feature flags: per-tenant evaluation with percentage rollout and variant support
CREATE TABLE IF NOT EXISTS feature_flags (
  id TEXT PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  flag_type TEXT DEFAULT 'boolean' CHECK(flag_type IN ('boolean', 'percentage', 'variant', 'tenant_list')),
  default_value TEXT DEFAULT 'false',
  enabled INTEGER DEFAULT 0,
  rollout_percentage INTEGER DEFAULT 0,
  variants TEXT DEFAULT '[]',
  tenant_overrides TEXT DEFAULT '{}',
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Flag evaluation log for analytics and debugging
CREATE TABLE IF NOT EXISTS flag_evaluations (
  id TEXT PRIMARY KEY,
  flag_key TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  result TEXT NOT NULL,
  evaluated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_flag_eval_key ON flag_evaluations(flag_key);
CREATE INDEX idx_flag_eval_tenant ON flag_evaluations(tenant_id);
