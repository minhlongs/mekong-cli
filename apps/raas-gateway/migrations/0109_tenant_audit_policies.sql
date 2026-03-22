CREATE TABLE IF NOT EXISTS audit_policies (
  id TEXT PRIMARY KEY DEFAULT ('ap_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  event_types TEXT NOT NULL DEFAULT '["*"]', -- JSON array: mission.created, auth.login, etc.
  retention_days INTEGER NOT NULL DEFAULT 90,
  log_level TEXT NOT NULL DEFAULT 'standard', -- minimal, standard, verbose
  include_request_body INTEGER NOT NULL DEFAULT 0,
  include_response_body INTEGER NOT NULL DEFAULT 0,
  export_enabled INTEGER NOT NULL DEFAULT 0,
  export_destination TEXT, -- s3, webhook, email
  export_config TEXT DEFAULT '{}', -- JSON
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ap_tenant ON audit_policies(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ap_name ON audit_policies(tenant_id, policy_name);

CREATE TABLE IF NOT EXISTS audit_policy_violations (
  id TEXT PRIMARY KEY DEFAULT ('apv_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  violation_type TEXT NOT NULL, -- retention_exceeded, unauthorized_access, policy_breach
  details TEXT DEFAULT '{}',
  severity TEXT NOT NULL DEFAULT 'warning', -- info, warning, critical
  resolved INTEGER NOT NULL DEFAULT 0,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_apv_tenant ON audit_policy_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_apv_policy ON audit_policy_violations(policy_id);
CREATE INDEX IF NOT EXISTS idx_apv_severity ON audit_policy_violations(severity, resolved);
