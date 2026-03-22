CREATE TABLE IF NOT EXISTS workflow_automations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workflow_name TEXT NOT NULL,
  trigger_event TEXT NOT NULL,
  condition_json TEXT DEFAULT '{}',
  action_type TEXT NOT NULL,
  action_config_json TEXT DEFAULT '{}',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_workflow_automations_tenant ON workflow_automations(tenant_id);

CREATE TABLE IF NOT EXISTS workflow_automation_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  trigger_data_json TEXT DEFAULT '{}',
  status TEXT DEFAULT 'pending',
  result_json TEXT,
  started_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_workflow_automation_runs_tenant ON workflow_automation_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_automation_runs_workflow ON workflow_automation_runs(workflow_id);
