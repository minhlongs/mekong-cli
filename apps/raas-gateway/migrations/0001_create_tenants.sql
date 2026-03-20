-- Migration: 0001_create_tenants
-- Created: 2026-03-19
-- Description: Create tenants table for RaaS license management

CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  tier TEXT DEFAULT 'starter' CHECK(tier IN ('starter', 'pro', 'enterprise')),
  active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
  expires_at INTEGER,  -- epoch ms, NULL = never expires
  used_credits INTEGER DEFAULT 0,
  billing_period_start INTEGER DEFAULT (strftime('%s', 'now') * 1000),
  settings TEXT DEFAULT '{}',  -- JSON settings
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Index for tenant lookups by email
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);

-- Index for active tenants
CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(active) WHERE active = 1;

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS update_tenants_updated_at
AFTER UPDATE ON tenants
BEGIN
  UPDATE tenants SET updated_at = datetime('now') WHERE id = NEW.id;
END;
