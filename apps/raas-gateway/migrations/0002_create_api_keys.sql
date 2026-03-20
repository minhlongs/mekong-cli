-- Migration: 0002_create_api_keys
-- Created: 2026-03-19
-- Description: Create API keys table for tenant authentication

CREATE TABLE IF NOT EXISTS api_keys (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL,
  name TEXT NOT NULL DEFAULT 'API Key',
  created_at TEXT DEFAULT (datetime('now')),
  last_used_at TEXT,
  revoked INTEGER DEFAULT 0 CHECK(revoked IN (0, 1)),
  permissions TEXT DEFAULT '[]'  -- JSON array of permissions
);

-- Index for API key lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Index for tenant's keys
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);

-- Index for active (non-revoked) keys
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(tenant_id, revoked) WHERE revoked = 0;
