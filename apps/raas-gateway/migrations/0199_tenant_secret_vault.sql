-- Migration: Tenant Secret Vault
-- Stores encrypted tenant secrets (API keys, tokens, etc.) with access audit logs

CREATE TABLE IF NOT EXISTS tenant_secrets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  secret_name TEXT NOT NULL,
  encrypted_value TEXT NOT NULL,
  secret_type TEXT DEFAULT 'api_key',
  expires_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenant_secrets_tenant_id ON tenant_secrets (tenant_id);

CREATE TABLE IF NOT EXISTS secret_access_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  secret_id TEXT NOT NULL,
  action TEXT DEFAULT 'read',
  ip_address TEXT,
  accessed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_secret_access_logs_tenant_id ON secret_access_logs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_secret_access_logs_secret_id ON secret_access_logs (secret_id);
