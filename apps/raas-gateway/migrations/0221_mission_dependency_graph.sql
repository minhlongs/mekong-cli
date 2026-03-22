-- Migration 0221: Mission Dependency Graph
-- Tables: mission_dependencies, mission_dependency_runs

CREATE TABLE IF NOT EXISTS mission_dependencies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  depends_on_mission_id TEXT NOT NULL,
  dependency_type TEXT NOT NULL DEFAULT 'required',
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_dependencies_tenant ON mission_dependencies(tenant_id);

CREATE TABLE IF NOT EXISTS mission_dependency_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  graph_id TEXT NOT NULL,
  execution_order TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_dependency_runs_tenant ON mission_dependency_runs(tenant_id);
