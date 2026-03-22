-- Migration: Mission artifact storage — files produced by missions + download audit log

CREATE TABLE IF NOT EXISTS mission_artifacts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  artifact_type TEXT NOT NULL DEFAULT 'output',
  file_name TEXT NOT NULL,
  file_size INTEGER NOT NULL DEFAULT 0,
  storage_path TEXT NOT NULL,
  content_type TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifact_downloads (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  artifact_id TEXT NOT NULL,
  downloaded_by TEXT NOT NULL,
  ip_address TEXT NOT NULL,
  downloaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_mission_artifacts_tenant_id
  ON mission_artifacts (tenant_id);

CREATE INDEX IF NOT EXISTS idx_mission_artifacts_mission_id
  ON mission_artifacts (mission_id);

CREATE INDEX IF NOT EXISTS idx_artifact_downloads_tenant_id
  ON artifact_downloads (tenant_id);

CREATE INDEX IF NOT EXISTS idx_artifact_downloads_artifact_id
  ON artifact_downloads (artifact_id);
