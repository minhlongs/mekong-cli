-- Migration: 0008_add_tier_values
-- Created: 2026-03-21
-- Description: Expand tier CHECK constraint to include free, agency, master

-- SQLite doesn't support ALTER CHECK constraints directly
-- Recreate table with expanded constraint via temp table

-- Step 1: Create temp with new constraint
CREATE TABLE IF NOT EXISTS tenants_new (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'starter', 'pro', 'agency', 'master', 'enterprise')),
  active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
  expires_at INTEGER,
  used_credits INTEGER DEFAULT 0,
  billing_period_start INTEGER DEFAULT (strftime('%s', 'now') * 1000),
  settings TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  balance INTEGER DEFAULT 0,
  total_earned INTEGER DEFAULT 0,
  total_spent INTEGER DEFAULT 0
);

-- Step 2: Copy data
INSERT INTO tenants_new SELECT * FROM tenants;

-- Step 3: Drop old, rename new
DROP TABLE tenants;
ALTER TABLE tenants_new RENAME TO tenants;

-- Step 4: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(active) WHERE active = 1;

-- Step 5: Recreate trigger
CREATE TRIGGER IF NOT EXISTS update_tenants_updated_at
AFTER UPDATE ON tenants
BEGIN
  UPDATE tenants SET updated_at = datetime('now') WHERE id = NEW.id;
END;
