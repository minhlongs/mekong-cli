-- Migration 0220: Tenant API Key Rotation
-- Tracks rotation schedules and history for tenant API keys

CREATE TABLE IF NOT EXISTS api_key_rotations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  key_name TEXT NOT NULL,
  rotation_interval_days INTEGER NOT NULL DEFAULT 90,
  last_rotated_at TEXT,
  next_rotation_at TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_key_rotations_tenant ON api_key_rotations(tenant_id);

CREATE TABLE IF NOT EXISTS api_key_rotation_history (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rotation_id TEXT NOT NULL,
  old_key_hash TEXT,
  new_key_hash TEXT,
  rotated_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_key_rotation_history_tenant ON api_key_rotation_history(tenant_id);
