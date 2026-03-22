-- Wave 55: Mission Dependency Graph for RaaS Gateway
-- Tables: mission_dependencies_v2, execution_groups, critical_path_analysis

CREATE TABLE IF NOT EXISTS mission_dependencies_v2 (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  parent_mission_id TEXT NOT NULL,
  child_mission_id TEXT NOT NULL,
  dependency_type TEXT DEFAULT 'finish_to_start',
  status TEXT DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (parent_mission_id, child_mission_id)
);

CREATE TABLE IF NOT EXISTS execution_groups (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  missions_json TEXT DEFAULT '[]',
  execution_order TEXT DEFAULT 'parallel',
  status TEXT DEFAULT 'pending',
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS critical_path_analysis (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  root_mission_id TEXT NOT NULL,
  path_json TEXT DEFAULT '[]',
  total_duration_ms INTEGER DEFAULT 0,
  bottleneck_mission_id TEXT,
  analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for mission_dependencies_v2
CREATE INDEX IF NOT EXISTS idx_mdv2_tenant_id ON mission_dependencies_v2(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mdv2_parent_mission_id ON mission_dependencies_v2(parent_mission_id);
CREATE INDEX IF NOT EXISTS idx_mdv2_child_mission_id ON mission_dependencies_v2(child_mission_id);

-- Indexes for execution_groups
CREATE INDEX IF NOT EXISTS idx_exec_groups_tenant_id ON execution_groups(tenant_id);

-- Indexes for critical_path_analysis
CREATE INDEX IF NOT EXISTS idx_cpa_tenant_id ON critical_path_analysis(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cpa_root_mission_id ON critical_path_analysis(root_mission_id);
