-- Migration 0118: Mission Approval Workflow
-- Multi-step approval chains before mission execution

CREATE TABLE IF NOT EXISTS approval_workflows (
  id TEXT PRIMARY KEY DEFAULT ('aw_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  steps_json TEXT NOT NULL DEFAULT '[]', -- JSON array of approval steps
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_tenant ON approval_workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_active ON approval_workflows(tenant_id, is_active);

CREATE TABLE IF NOT EXISTS approval_requests (
  id TEXT PRIMARY KEY DEFAULT ('ar_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  current_step INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', -- pending/approved/rejected/escalated
  requested_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_approval_requests_tenant ON approval_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_workflow ON approval_requests(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_mission ON approval_requests(mission_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(tenant_id, status);

CREATE TABLE IF NOT EXISTS approval_decisions (
  id TEXT PRIMARY KEY DEFAULT ('ad_' || lower(hex(randomblob(8)))),
  request_id TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  approver_id TEXT NOT NULL,
  decision TEXT NOT NULL, -- approve/reject/delegate
  comment TEXT,
  decided_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_approval_decisions_request ON approval_decisions(request_id);
CREATE INDEX IF NOT EXISTS idx_approval_decisions_approver ON approval_decisions(approver_id);
