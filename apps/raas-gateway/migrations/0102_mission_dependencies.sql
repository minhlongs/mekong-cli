-- Wave 41: Mission Dependencies (DAG) — chain missions with dependency resolution
-- Allows missions to depend on other missions completing first

CREATE TABLE IF NOT EXISTS mission_chains (
  id TEXT PRIMARY KEY DEFAULT ('mc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'draft', -- draft, active, running, completed, failed, cancelled
  total_missions INTEGER NOT NULL DEFAULT 0,
  completed_missions INTEGER NOT NULL DEFAULT 0,
  failed_missions INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_mc_tenant ON mission_chains(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mc_status ON mission_chains(tenant_id, status);

CREATE TABLE IF NOT EXISTS mission_dependencies (
  id TEXT PRIMARY KEY DEFAULT ('md_' || lower(hex(randomblob(8)))),
  chain_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  depends_on_mission_id TEXT, -- NULL = root node
  tenant_id TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, ready, running, completed, failed, skipped
  mission_config TEXT DEFAULT '{}', -- JSON mission parameters
  result TEXT, -- JSON result from completed mission
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_md_chain ON mission_dependencies(chain_id);
CREATE INDEX IF NOT EXISTS idx_md_mission ON mission_dependencies(mission_id);
CREATE INDEX IF NOT EXISTS idx_md_depends ON mission_dependencies(depends_on_mission_id);
CREATE INDEX IF NOT EXISTS idx_md_tenant ON mission_dependencies(tenant_id);
