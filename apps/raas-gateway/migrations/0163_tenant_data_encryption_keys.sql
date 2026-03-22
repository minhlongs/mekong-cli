-- Migration 0163: Tenant Data Encryption Keys
-- Tables: encryption_keys (keyed), key_usage_logs

CREATE TABLE IF NOT EXISTS encryption_keys (
  id TEXT PRIMARY KEY DEFAULT ('dek_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  key_name TEXT NOT NULL,
  algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
  key_version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  rotated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_dek_tenant ON encryption_keys(tenant_id);

CREATE TABLE IF NOT EXISTS key_usage_logs (
  id TEXT PRIMARY KEY DEFAULT ('kul_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  key_id TEXT NOT NULL,
  operation TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_kul_tenant ON key_usage_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kul_key ON key_usage_logs(key_id);
