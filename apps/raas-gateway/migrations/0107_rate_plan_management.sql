-- Migration 0107: Rate Plan Management
-- Introduces rate_plans and tenant_rate_plan_assignments tables

CREATE TABLE IF NOT EXISTS rate_plans (
  id TEXT PRIMARY KEY DEFAULT ('rp_' || lower(hex(randomblob(8)))),
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  tier TEXT NOT NULL DEFAULT 'custom', -- starter, pro, enterprise, custom
  requests_per_minute INTEGER NOT NULL DEFAULT 60,
  requests_per_hour INTEGER NOT NULL DEFAULT 1000,
  requests_per_day INTEGER NOT NULL DEFAULT 10000,
  burst_limit INTEGER NOT NULL DEFAULT 100,
  concurrent_limit INTEGER NOT NULL DEFAULT 10,
  is_default INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rp_tier ON rate_plans(tier);
CREATE INDEX IF NOT EXISTS idx_rp_default ON rate_plans(is_default, is_active);

CREATE TABLE IF NOT EXISTS tenant_rate_plan_assignments (
  id TEXT PRIMARY KEY DEFAULT ('trpa_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  rate_plan_id TEXT NOT NULL,
  override_rpm INTEGER, -- override requests_per_minute
  override_rph INTEGER, -- override requests_per_hour
  override_rpd INTEGER, -- override requests_per_day
  assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT,
  assigned_by TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_trpa_tenant ON tenant_rate_plan_assignments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_trpa_plan ON tenant_rate_plan_assignments(rate_plan_id);
