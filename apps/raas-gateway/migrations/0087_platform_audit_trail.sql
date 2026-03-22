-- Migration 0087: Platform Audit Trail
-- Admin action logging, change tracking, compliance audit for platform operations

CREATE TABLE IF NOT EXISTS platform_audit_entries (
  id TEXT PRIMARY KEY,
  actor_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  changes TEXT DEFAULT '{}',
  metadata TEXT DEFAULT '{}',
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_retention_configs (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL UNIQUE,
  retention_days INTEGER DEFAULT 365,
  is_immutable INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_actor ON platform_audit_entries(actor_id, created_at);
CREATE INDEX idx_audit_resource ON platform_audit_entries(resource_type, resource_id);
CREATE INDEX idx_audit_action ON platform_audit_entries(action, created_at);
CREATE INDEX idx_audit_created ON platform_audit_entries(created_at);
