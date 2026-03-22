-- Migration 0092: Migration tools for competitor platform onboarding
-- Supports bulk import/export of tenant data

CREATE TABLE IF NOT EXISTS migration_jobs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  direction TEXT NOT NULL, -- import, export
  source_platform TEXT, -- zapier, make, n8n, custom
  status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
  total_records INTEGER DEFAULT 0,
  processed_records INTEGER DEFAULT 0,
  failed_records INTEGER DEFAULT 0,
  error_log TEXT, -- JSON array of errors
  data_types TEXT, -- JSON array: missions, templates, settings, team, webhooks
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_migration_tenant ON migration_jobs(tenant_id);
CREATE INDEX idx_migration_status ON migration_jobs(status);

CREATE TABLE IF NOT EXISTS migration_mappings (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_mapping_job ON migration_mappings(job_id);
