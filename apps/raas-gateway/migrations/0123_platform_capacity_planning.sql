-- Migration 0123: Platform Capacity Planning
-- Capacity forecasting, resource allocation tracking, and scaling recommendations

CREATE TABLE IF NOT EXISTS capacity_snapshots (
  id TEXT PRIMARY KEY DEFAULT ('snap_' || lower(hex(randomblob(8)))),
  resource_type TEXT NOT NULL CHECK (resource_type IN ('compute', 'storage', 'bandwidth', 'api_calls')),
  current_usage REAL NOT NULL DEFAULT 0,
  max_capacity REAL NOT NULL DEFAULT 0,
  utilization_pct REAL NOT NULL DEFAULT 0,
  recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_capacity_snapshots_resource_type ON capacity_snapshots(resource_type);
CREATE INDEX IF NOT EXISTS idx_capacity_snapshots_recorded_at ON capacity_snapshots(recorded_at);
CREATE INDEX IF NOT EXISTS idx_capacity_snapshots_resource_recorded ON capacity_snapshots(resource_type, recorded_at);

CREATE TABLE IF NOT EXISTS capacity_forecasts (
  id TEXT PRIMARY KEY DEFAULT ('fcst_' || lower(hex(randomblob(8)))),
  resource_type TEXT NOT NULL CHECK (resource_type IN ('compute', 'storage', 'bandwidth', 'api_calls')),
  forecast_date TEXT NOT NULL,
  predicted_usage REAL NOT NULL DEFAULT 0,
  confidence_pct REAL NOT NULL DEFAULT 0,
  model_version TEXT NOT NULL DEFAULT 'v1',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_capacity_forecasts_resource_type ON capacity_forecasts(resource_type);
CREATE INDEX IF NOT EXISTS idx_capacity_forecasts_forecast_date ON capacity_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_capacity_forecasts_resource_date ON capacity_forecasts(resource_type, forecast_date);

CREATE TABLE IF NOT EXISTS scaling_recommendations (
  id TEXT PRIMARY KEY DEFAULT ('rec_' || lower(hex(randomblob(8)))),
  resource_type TEXT NOT NULL CHECK (resource_type IN ('compute', 'storage', 'bandwidth', 'api_calls')),
  recommendation_type TEXT NOT NULL CHECK (recommendation_type IN ('scale_up', 'scale_down', 'optimize', 'no_action')),
  current_value REAL NOT NULL DEFAULT 0,
  recommended_value REAL NOT NULL DEFAULT 0,
  reason TEXT NOT NULL DEFAULT '',
  priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'implemented')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_scaling_recs_resource_type ON scaling_recommendations(resource_type);
CREATE INDEX IF NOT EXISTS idx_scaling_recs_status ON scaling_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_scaling_recs_priority ON scaling_recommendations(priority);
CREATE INDEX IF NOT EXISTS idx_scaling_recs_status_priority ON scaling_recommendations(status, priority);
