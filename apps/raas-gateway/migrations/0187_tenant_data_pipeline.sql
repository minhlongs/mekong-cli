CREATE TABLE IF NOT EXISTS data_pipelines (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, pipeline_name TEXT NOT NULL,
  source_type TEXT NOT NULL, destination_type TEXT NOT NULL,
  transform_config_json TEXT DEFAULT '{}', schedule_cron TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_data_pipelines_tenant ON data_pipelines(tenant_id);

CREATE TABLE IF NOT EXISTS data_pipeline_runs (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, pipeline_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', records_processed INTEGER DEFAULT 0,
  records_failed INTEGER DEFAULT 0, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT, error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_data_pipeline_runs_tenant ON data_pipeline_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_data_pipeline_runs_pipeline ON data_pipeline_runs(pipeline_id);
