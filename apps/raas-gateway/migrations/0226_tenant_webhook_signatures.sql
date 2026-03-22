-- Migration 0226: Tenant Webhook Signatures
-- Stores signing keys and verification logs for tenant webhook security

CREATE TABLE IF NOT EXISTS webhook_signing_keys (
  id         TEXT NOT NULL PRIMARY KEY,
  tenant_id  TEXT NOT NULL,
  key_name   TEXT NOT NULL,
  secret_hash TEXT NOT NULL,
  algorithm  TEXT NOT NULL DEFAULT 'hmac-sha256',
  status     TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_signing_keys_tenant ON webhook_signing_keys(tenant_id);

CREATE TABLE IF NOT EXISTS webhook_signature_logs (
  id             TEXT NOT NULL PRIMARY KEY,
  tenant_id      TEXT NOT NULL,
  signing_key_id TEXT NOT NULL,
  webhook_url    TEXT,
  verified       INTEGER NOT NULL DEFAULT 0,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_signature_logs_tenant ON webhook_signature_logs(tenant_id);
