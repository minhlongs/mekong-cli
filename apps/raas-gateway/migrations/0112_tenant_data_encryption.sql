-- Migration 0112: Tenant Data Encryption
-- Tables: encryption_keys, encryption_audit, encrypted_fields

CREATE TABLE IF NOT EXISTS encryption_keys (
  id TEXT PRIMARY KEY DEFAULT ('ek_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  key_alias TEXT NOT NULL,
  key_type TEXT NOT NULL DEFAULT 'aes-256-gcm', -- aes-256-gcm, rsa-2048
  key_status TEXT NOT NULL DEFAULT 'active', -- active, rotating, retired, revoked
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  rotated_at TEXT,
  expires_at TEXT,
  version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_enc_keys_tenant ON encryption_keys(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_enc_keys_alias ON encryption_keys(tenant_id, key_alias);

CREATE TABLE IF NOT EXISTS encryption_audit (
  id TEXT PRIMARY KEY DEFAULT ('ea_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  key_id TEXT NOT NULL,
  operation TEXT NOT NULL, -- encrypt, decrypt, rotate, revoke
  field_name TEXT,
  performed_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_enc_audit_tenant ON encryption_audit(tenant_id);
CREATE INDEX IF NOT EXISTS idx_enc_audit_key ON encryption_audit(key_id);

CREATE TABLE IF NOT EXISTS encrypted_fields (
  id TEXT PRIMARY KEY DEFAULT ('ef_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  table_name TEXT NOT NULL,
  field_name TEXT NOT NULL,
  key_id TEXT NOT NULL,
  encryption_type TEXT NOT NULL DEFAULT 'deterministic', -- deterministic, randomized
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_enc_fields_tenant ON encrypted_fields(tenant_id);
