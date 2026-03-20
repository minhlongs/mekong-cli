-- Migration: 0003_create_missions
-- Created: 2026-03-19
-- Description: Create missions table for tracking agent missions

CREATE TABLE IF NOT EXISTS missions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  goal TEXT NOT NULL,
  complexity TEXT DEFAULT 'standard' CHECK(complexity IN ('simple', 'standard', 'complex')),
  status TEXT DEFAULT 'queued' CHECK(status IN (
    'queued', 'planning', 'executing', 'verifying',
    'completed', 'failed', 'cancelled'
  )),
  credits_cost INTEGER DEFAULT 0,
  project TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  started_at TEXT,
  completed_at TEXT,
  error_message TEXT
);

-- Index for tenant's missions (most common query)
CREATE INDEX IF NOT EXISTS idx_missions_tenant ON missions(tenant_id, created_at DESC);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);

-- Index for pending missions (queue processing)
CREATE INDEX IF NOT EXISTS idx_missions_pending ON missions(status, created_at)
WHERE status IN ('queued', 'planning', 'executing');

-- Composite index for tenant status queries
CREATE INDEX IF NOT EXISTS idx_missions_tenant_status ON missions(tenant_id, status);
