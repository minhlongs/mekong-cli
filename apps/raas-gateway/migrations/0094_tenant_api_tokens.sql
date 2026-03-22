-- Migration 0094: Tenant API Tokens
-- Long-lived service tokens with scoped permissions, rotation, and expiry management

CREATE TABLE IF NOT EXISTS tenant_api_tokens (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  token_prefix TEXT NOT NULL, -- first 8 chars for display
  scopes TEXT NOT NULL DEFAULT '["read"]', -- JSON array: read, write, admin, missions, billing
  expires_at TEXT,
  last_used_at TEXT,
  last_used_ip TEXT,
  usage_count INTEGER DEFAULT 0,
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  rotated_from TEXT -- previous token ID if rotated
);

CREATE INDEX idx_api_tokens_tenant ON tenant_api_tokens(tenant_id);
CREATE INDEX idx_api_tokens_hash ON tenant_api_tokens(token_hash);
CREATE INDEX idx_api_tokens_active ON tenant_api_tokens(is_active);
