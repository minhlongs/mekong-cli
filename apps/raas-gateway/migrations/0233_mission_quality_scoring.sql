-- Mission Quality Scoring — per-mission accuracy, completeness, timeliness scores
-- and configurable per-tenant scoring criteria with weights

CREATE TABLE IF NOT EXISTS mission_quality_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  accuracy_score REAL,
  completeness_score REAL,
  timeliness_score REAL,
  overall_score REAL,
  scored_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_quality_scores_tenant ON mission_quality_scores(tenant_id);

CREATE TABLE IF NOT EXISTS mission_quality_criteria (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  criteria_name TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_quality_criteria_tenant ON mission_quality_criteria(tenant_id);
