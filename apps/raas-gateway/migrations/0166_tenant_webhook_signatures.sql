-- Migration: Tenant Webhook Signatures
-- Tables for managing tenant webhook HMAC signatures and verification logs

CREATE TABLE IF NOT EXISTS webhook_signatures (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  algorithm TEXT NOT NULL DEFAULT 'sha256',
  secret_key TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhook_signatures_tenant_id ON webhook_signatures (tenant_id);

CREATE TABLE IF NOT EXISTS signature_verifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  signature_id TEXT NOT NULL,
  webhook_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'valid',
  verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signature_verifications_tenant_id ON signature_verifications (tenant_id);
