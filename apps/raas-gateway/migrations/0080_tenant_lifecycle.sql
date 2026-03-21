-- Migration 0080: Tenant Lifecycle Management
-- Tracks lifecycle stages and automated transitions for tenants

CREATE TABLE IF NOT EXISTS tenant_lifecycle (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  stage TEXT DEFAULT 'trial',
  previous_stage TEXT,
  stage_entered_at TEXT DEFAULT (datetime('now')),
  trial_ends_at TEXT,
  last_activity_at TEXT,
  risk_score REAL DEFAULT 0,
  health_indicators TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lifecycle_transitions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  from_stage TEXT NOT NULL,
  to_stage TEXT NOT NULL,
  reason TEXT,
  triggered_by TEXT DEFAULT 'system',
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_tenant ON tenant_lifecycle(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_stage ON tenant_lifecycle(stage);
CREATE INDEX IF NOT EXISTS idx_lifecycle_risk ON tenant_lifecycle(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_transitions_tenant ON lifecycle_transitions(tenant_id);
