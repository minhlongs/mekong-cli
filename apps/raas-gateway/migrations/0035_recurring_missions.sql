-- Migration: 0035_recurring_missions
-- Created: 2026-03-21
-- Description: Create recurring_missions table for scheduled/cron-based mission execution

CREATE TABLE IF NOT EXISTS recurring_missions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  input TEXT NOT NULL DEFAULT '{}',
  cron_expression TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'UTC',
  is_active INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  next_run_at TEXT,
  run_count INTEGER NOT NULL DEFAULT 0,
  max_runs INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Index for scheduler: find active missions due for execution
CREATE INDEX idx_recurring_active ON recurring_missions(is_active, next_run_at);

-- Index for tenant-scoped queries
CREATE INDEX idx_recurring_tenant ON recurring_missions(tenant_id);
