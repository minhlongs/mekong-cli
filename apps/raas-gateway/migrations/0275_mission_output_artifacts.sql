-- Mission Output Artifacts — store files/outputs produced by missions
-- Downloads tracking for audit and analytics

CREATE TABLE IF NOT EXISTS mission_output_artifacts (
  id           TEXT    PRIMARY KEY,
  tenant_id    TEXT    NOT NULL,
  mission_id   TEXT    NOT NULL,
  artifact_name TEXT   NOT NULL,
  artifact_type TEXT   NOT NULL DEFAULT 'file',
  file_url     TEXT,
  file_size    INTEGER,
  content_type TEXT,
  created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_output_artifacts_tenant ON mission_output_artifacts(tenant_id);

CREATE TABLE IF NOT EXISTS mission_artifact_downloads (
  id            TEXT PRIMARY KEY,
  tenant_id     TEXT NOT NULL,
  artifact_id   TEXT NOT NULL,
  downloaded_by TEXT,
  downloaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_artifact_downloads_artifact ON mission_artifact_downloads(artifact_id);
