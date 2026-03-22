-- Migration 0217: Tenant Consent Management
-- Consent records and policy definitions per tenant

CREATE TABLE IF NOT EXISTS consent_records (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  user_id TEXT,
  consent_type TEXT NOT NULL,
  purpose TEXT,
  granted INTEGER NOT NULL DEFAULT 1,
  ip_address TEXT,
  granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
  revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS consent_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  policy_name TEXT,
  policy_text TEXT,
  version TEXT DEFAULT '1.0',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_consent_records_tenant_id
  ON consent_records (tenant_id);

CREATE INDEX IF NOT EXISTS idx_consent_records_user_id
  ON consent_records (user_id);

CREATE INDEX IF NOT EXISTS idx_consent_records_consent_type
  ON consent_records (consent_type);

CREATE INDEX IF NOT EXISTS idx_consent_policies_tenant_id
  ON consent_policies (tenant_id);
