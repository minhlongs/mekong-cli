-- Migration 0127: Platform Audit Trail (Wave 50)
-- Centralized audit log with retention policies and export capabilities

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  actor_id TEXT,
  actor_type TEXT DEFAULT 'user',
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  details_json TEXT DEFAULT '{}',
  ip_address TEXT,
  user_agent TEXT,
  severity TEXT DEFAULT 'info',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_retention_policies (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL UNIQUE,
  retention_days INTEGER DEFAULT 90,
  auto_archive INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_exports (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  filters_json TEXT DEFAULT '{}',
  status TEXT DEFAULT 'pending',
  file_url TEXT,
  record_count INTEGER DEFAULT 0,
  requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
