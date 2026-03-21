-- Migration 0044: mission model usage tracking
-- Tracks which AI model was used for each mission, with performance and cost data

CREATE TABLE IF NOT EXISTS mission_model_usage (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  tenant_id TEXT,
  model_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  tokens_used INTEGER DEFAULT 0,
  latency_ms INTEGER DEFAULT 0,
  cost_estimate REAL DEFAULT 0,
  status TEXT DEFAULT 'success',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_model_usage_mission ON mission_model_usage(mission_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_tenant ON mission_model_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_model ON mission_model_usage(model_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_created ON mission_model_usage(created_at);
