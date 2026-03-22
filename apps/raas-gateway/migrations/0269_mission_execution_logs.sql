-- Mission execution logs: per-step structured log entries for mission runs
CREATE TABLE IF NOT EXISTS mission_execution_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  step_name TEXT NOT NULL,
  log_level TEXT NOT NULL DEFAULT 'info',
  message TEXT NOT NULL,
  metadata TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_execution_logs_tenant ON mission_execution_logs(tenant_id);

-- Mission execution summaries: aggregated stats per mission run
CREATE TABLE IF NOT EXISTS mission_execution_summaries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  total_steps INTEGER DEFAULT 0,
  completed_steps INTEGER DEFAULT 0,
  failed_steps INTEGER DEFAULT 0,
  total_duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_execution_summaries_tenant ON mission_execution_summaries(tenant_id);
