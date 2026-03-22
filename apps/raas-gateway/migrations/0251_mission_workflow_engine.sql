-- Mission Workflow Engine: multi-step workflow definitions and execution tracking

CREATE TABLE IF NOT EXISTS mission_workflows (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workflow_name TEXT NOT NULL,
  trigger_event TEXT NOT NULL,
  steps_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_workflows_tenant ON mission_workflows(tenant_id);

CREATE TABLE IF NOT EXISTS mission_workflow_executions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  trigger_data TEXT,
  current_step INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'running',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE INDEX idx_mission_workflow_executions_tenant ON mission_workflow_executions(tenant_id);
