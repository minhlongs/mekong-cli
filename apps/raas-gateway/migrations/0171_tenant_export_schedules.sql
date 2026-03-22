-- Migration: Tenant Export Schedules
-- Stores recurring export schedule configs and run history per tenant

CREATE TABLE IF NOT EXISTS export_schedules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  export_type TEXT NOT NULL,
  format TEXT NOT NULL DEFAULT 'csv',
  cron_expression TEXT NOT NULL,
  destination TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_export_schedules_tenant_id ON export_schedules (tenant_id);

CREATE TABLE IF NOT EXISTS export_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  schedule_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  records_exported INTEGER NOT NULL DEFAULT 0,
  file_size_bytes INTEGER,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_export_runs_tenant_id ON export_runs (tenant_id);
