-- Wave 62: Platform Audit Policies
-- Tables: audit_policies, audit_policy_violations

CREATE TABLE IF NOT EXISTS audit_policies (
  id TEXT PRIMARY KEY,
  policy_name TEXT NOT NULL,
  description TEXT,
  event_types TEXT,
  retention_days INTEGER DEFAULT 365,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_policy_violations (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  violation_type TEXT NOT NULL,
  details TEXT,
  severity TEXT DEFAULT 'medium',
  resolved INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_audit_policies_policy_name ON audit_policies(policy_name);
CREATE INDEX IF NOT EXISTS idx_audit_policy_violations_policy_id ON audit_policy_violations(policy_id);
CREATE INDEX IF NOT EXISTS idx_audit_policy_violations_tenant_id ON audit_policy_violations(tenant_id);
