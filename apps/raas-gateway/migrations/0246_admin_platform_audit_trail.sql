-- Admin Platform Audit Trail
-- Tables: platform_audit_entries, platform_audit_policies

CREATE TABLE IF NOT EXISTS platform_audit_entries (
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  details TEXT,
  ip_address TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_audit_entries_actor ON platform_audit_entries(actor);

CREATE TABLE IF NOT EXISTS platform_audit_policies (
  id TEXT PRIMARY KEY,
  policy_name TEXT NOT NULL,
  retention_days INTEGER NOT NULL DEFAULT 365,
  log_level TEXT NOT NULL DEFAULT 'info',
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_audit_policies_name ON platform_audit_policies(policy_name);
