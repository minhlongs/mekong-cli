-- Dunning System: Add license status tracking
-- Adds dunning_status column to tenants table for suspension tracking

-- Add dunning_status column to tenants table
ALTER TABLE tenants ADD COLUMN dunning_status TEXT CHECK (dunning_status IN ('suspended', 'blocked'));

-- Add index for quick license status checks
CREATE INDEX IF NOT EXISTS idx_tenants_dunning_status ON tenants(dunning_status);

-- Audit logs table for compliance tracking
CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  user_id TEXT,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  resource_id TEXT,
  old_value TEXT,
  new_value TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- License keys table for RaaS license management
CREATE TABLE IF NOT EXISTS license_keys (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  key_hash TEXT UNIQUE NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'revoked', 'expired')),
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_license_keys_hash ON license_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_license_keys_tenant ON license_keys(tenant_id);
