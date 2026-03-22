-- Wave 57: Mission Result Storage for RaaS Gateway
-- Tables: mission_results, result_attachments

CREATE TABLE IF NOT EXISTS mission_results (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  result_type TEXT DEFAULT 'text',
  content TEXT,
  metadata_json TEXT DEFAULT '{}',
  version INTEGER DEFAULT 1,
  size_bytes INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS result_attachments (
  id TEXT PRIMARY KEY,
  result_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  content_type TEXT DEFAULT 'application/octet-stream',
  size_bytes INTEGER DEFAULT 0,
  storage_url TEXT,
  checksum TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for mission_results
CREATE INDEX IF NOT EXISTS idx_mission_results_tenant_id ON mission_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_results_mission_id ON mission_results(mission_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mission_results_mission_version ON mission_results(mission_id, version);

-- Indexes for result_attachments
CREATE INDEX IF NOT EXISTS idx_result_attachments_result_id ON result_attachments(result_id);
