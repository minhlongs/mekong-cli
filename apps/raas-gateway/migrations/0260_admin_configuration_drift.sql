-- Migration: configuration drift detection and baselines
-- Tracks detected drifts between expected and actual resource configurations

CREATE TABLE IF NOT EXISTS configuration_drift_detections (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  expected_value TEXT,
  actual_value TEXT,
  drift_type TEXT NOT NULL DEFAULT 'modified',
  severity TEXT NOT NULL DEFAULT 'medium',
  detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_drift_resource ON configuration_drift_detections(resource_type);

CREATE TABLE IF NOT EXISTS configuration_drift_baselines (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  baseline_config TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_drift_baselines_resource ON configuration_drift_baselines(resource_type);
