-- Mission Scheduling Engine tables
-- Wave 51: Cron-based job scheduler with execution tracking and skip rules

CREATE TABLE IF NOT EXISTS scheduled_jobs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  cron_expression TEXT NOT NULL,
  timezone TEXT DEFAULT 'UTC',
  mission_config_json TEXT NOT NULL DEFAULT '{}',
  status TEXT DEFAULT 'active',
  next_run_at TEXT,
  last_run_at TEXT,
  run_count INTEGER DEFAULT 0,
  max_runs INTEGER,
  skip_if_running INTEGER DEFAULT 1,
  execution_window_minutes INTEGER DEFAULT 60,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_executions (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  status TEXT DEFAULT 'running',
  started_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  duration_ms INTEGER,
  result_json TEXT,
  error TEXT,
  mission_id TEXT
);

CREATE TABLE IF NOT EXISTS skip_rules (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  rule_type TEXT NOT NULL,
  rule_config_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_tenant_id ON scheduled_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status ON scheduled_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_next_run_at ON scheduled_jobs(next_run_at);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_tenant_id ON job_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
CREATE INDEX IF NOT EXISTS idx_skip_rules_job_id ON skip_rules(job_id);
