-- Wave 29.2: Scheduled Missions (Cron Jobs) for RaaS Gateway
-- Creates scheduled_missions and scheduled_mission_runs tables

CREATE TABLE IF NOT EXISTS scheduled_missions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  cron_expression TEXT NOT NULL,
  timezone TEXT DEFAULT 'UTC',
  mission_config TEXT NOT NULL, -- JSON: { goal, complexity, model, project_id }
  status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','completed','failed')),
  last_run_at TEXT,
  next_run_at TEXT,
  run_count INTEGER DEFAULT 0,
  max_runs INTEGER, -- NULL = unlimited
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_scheduled_missions_tenant ON scheduled_missions(tenant_id);
CREATE INDEX idx_scheduled_missions_status ON scheduled_missions(tenant_id, status);
CREATE INDEX idx_scheduled_missions_next_run ON scheduled_missions(next_run_at);

CREATE TABLE IF NOT EXISTS scheduled_mission_runs (
  id TEXT PRIMARY KEY,
  scheduled_mission_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  mission_id TEXT, -- references missions table
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','skipped')),
  started_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  error TEXT
);

CREATE INDEX idx_scheduled_runs_mission ON scheduled_mission_runs(scheduled_mission_id);
