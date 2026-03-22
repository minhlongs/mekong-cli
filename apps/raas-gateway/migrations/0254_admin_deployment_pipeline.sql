-- Migration 0254: Admin deployment pipeline tables
-- Tracks CI/CD pipelines and their run history

CREATE TABLE IF NOT EXISTS deployment_pipelines (
  id TEXT PRIMARY KEY,
  pipeline_name TEXT NOT NULL,
  environment TEXT NOT NULL DEFAULT 'production',
  stages_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'idle',
  last_run_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_deployment_pipelines_env ON deployment_pipelines(environment);

CREATE TABLE IF NOT EXISTS deployment_pipeline_runs (
  id TEXT PRIMARY KEY,
  pipeline_id TEXT NOT NULL,
  triggered_by TEXT,
  current_stage TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE INDEX idx_deployment_pipeline_runs_pipeline ON deployment_pipeline_runs(pipeline_id);
