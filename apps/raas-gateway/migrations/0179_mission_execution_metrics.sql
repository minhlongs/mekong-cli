-- Migration: Mission Execution Metrics
CREATE TABLE IF NOT EXISTS mission_execution_metrics (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  execution_time_ms INTEGER NOT NULL,
  tokens_used INTEGER DEFAULT 0,
  model_used TEXT,
  success INTEGER NOT NULL DEFAULT 1,
  error_type TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mission_exec_metrics_tenant ON mission_execution_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_exec_metrics_mission ON mission_execution_metrics(mission_id);

CREATE TABLE IF NOT EXISTS mission_execution_aggregates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  total_executions INTEGER NOT NULL DEFAULT 0,
  avg_execution_time_ms REAL DEFAULT 0,
  p95_execution_time_ms INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  success_rate REAL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mission_exec_agg_tenant ON mission_execution_aggregates(tenant_id);
