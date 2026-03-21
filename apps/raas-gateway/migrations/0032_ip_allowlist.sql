-- Migration: 0032_ip_allowlist
-- Created: 2026-03-21
-- Description: IP allowlist per tenant — empty = allow all; entries = allowlist mode

CREATE TABLE IF NOT EXISTS ip_allowlist (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  cidr TEXT NOT NULL,
  label TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_ip_allowlist_tenant ON ip_allowlist(tenant_id);

-- Add batch_id and priority columns to missions for batch submission feature
ALTER TABLE missions ADD COLUMN batch_id TEXT;
ALTER TABLE missions ADD COLUMN priority INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_missions_batch ON missions(batch_id) WHERE batch_id IS NOT NULL;
