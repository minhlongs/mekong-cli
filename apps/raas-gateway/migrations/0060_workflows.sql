-- Migration: Custom Workflow Builder
-- Workflow definitions (DAGs) and execution tracking

CREATE TABLE IF NOT EXISTS workflows (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  steps TEXT NOT NULL DEFAULT '[]',
  trigger_type TEXT DEFAULT 'manual' CHECK(trigger_type IN ('manual', 'event', 'schedule', 'webhook')),
  trigger_config TEXT DEFAULT '{}',
  status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'paused', 'archived')),
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(tenant_id, status);

-- Workflow executions
CREATE TABLE IF NOT EXISTS workflow_executions (
  id TEXT PRIMARY KEY,
  workflow_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  status TEXT DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
  current_step INTEGER DEFAULT 0,
  step_results TEXT DEFAULT '[]',
  input_data TEXT DEFAULT '{}',
  output_data TEXT,
  started_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_wf_exec_workflow ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_wf_exec_tenant ON workflow_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wf_exec_status ON workflow_executions(tenant_id, status);
