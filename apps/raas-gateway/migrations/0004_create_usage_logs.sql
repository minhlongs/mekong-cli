-- Migration: 0004_create_usage_logs
-- Created: 2026-03-19
-- Description: Create usage logs table for credit audit trail

CREATE TABLE IF NOT EXISTS usage_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  mission_id TEXT REFERENCES missions(id) ON DELETE SET NULL,
  credits_cost INTEGER NOT NULL,
  timestamp TEXT DEFAULT (datetime('now')),
  success INTEGER DEFAULT 1 CHECK(success IN (0, 1)),
  metadata TEXT DEFAULT '{}'  -- JSON metadata
);

-- Index for tenant usage queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_tenant ON usage_logs(tenant_id, timestamp DESC);

-- Index for mission usage
CREATE INDEX IF NOT EXISTS idx_usage_logs_mission ON usage_logs(mission_id);

-- Index for successful usage (billing)
CREATE INDEX IF NOT EXISTS idx_usage_logs_success ON usage_logs(tenant_id, success) WHERE success = 1;
