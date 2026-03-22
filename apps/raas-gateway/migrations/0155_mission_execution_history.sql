-- Wave 59: Mission Execution History for RaaS Gateway
-- Tables: execution_history, execution_metrics

CREATE TABLE IF NOT EXISTS execution_history (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT,
  executor_type TEXT,
  status TEXT DEFAULT 'completed',
  duration_ms INTEGER,
  input_summary TEXT,
  output_summary TEXT,
  error_message TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_metrics (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT,
  metric_type TEXT NOT NULL,
  metric_value REAL NOT NULL,
  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for execution_history
CREATE INDEX IF NOT EXISTS idx_execution_history_tenant_id ON execution_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_mission_id ON execution_history(mission_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_created_at ON execution_history(created_at);

-- Indexes for execution_metrics
CREATE INDEX IF NOT EXISTS idx_execution_metrics_tenant_id ON execution_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_execution_metrics_mission_id ON execution_metrics(mission_id);
CREATE INDEX IF NOT EXISTS idx_execution_metrics_recorded_at ON execution_metrics(recorded_at);
