-- Mission Chain Orchestration — multi-step mission sequences with run tracking

CREATE TABLE IF NOT EXISTS mission_chains (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  chain_name  TEXT NOT NULL,
  steps_json  TEXT NOT NULL DEFAULT '[]',
  status      TEXT DEFAULT 'active',
  max_retries INTEGER DEFAULT 3,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_chains_tenant ON mission_chains(tenant_id);

CREATE TABLE IF NOT EXISTS mission_chain_runs (
  id           TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL,
  chain_id     TEXT NOT NULL,
  current_step INTEGER DEFAULT 0,
  status       TEXT DEFAULT 'pending',
  results_json TEXT DEFAULT '[]',
  started_at   TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_mission_chain_runs_tenant ON mission_chain_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_chain_runs_chain  ON mission_chain_runs(chain_id);
