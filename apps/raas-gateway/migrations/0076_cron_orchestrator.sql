-- Migration 0076: Cron Orchestrator — centralized scheduled task management
CREATE TABLE IF NOT EXISTS cron_jobs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  job_type TEXT NOT NULL,
  schedule TEXT NOT NULL,
  last_run_at TEXT,
  next_run_at TEXT,
  status TEXT DEFAULT 'active',
  config TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cron_execution_logs (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  started_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  status TEXT DEFAULT 'running',
  result TEXT,
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_cron_jobs_next ON cron_jobs(next_run_at, status);
CREATE INDEX IF NOT EXISTS idx_cron_jobs_type ON cron_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_cron_logs_job ON cron_execution_logs(job_id);
