-- Migration 0074: Usage Forecasting tables
-- Stores daily usage snapshots and ML-lite forecasts for capacity planning

CREATE TABLE IF NOT EXISTS usage_snapshots (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  metric_type TEXT NOT NULL, -- missions, credits, api_calls, storage
  metric_value REAL NOT NULL,
  snapshot_date TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_snap_tenant_type_date
  ON usage_snapshots(tenant_id, metric_type, snapshot_date);

CREATE INDEX IF NOT EXISTS idx_usage_snap_tenant
  ON usage_snapshots(tenant_id);

CREATE TABLE IF NOT EXISTS usage_forecasts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  forecast_date TEXT NOT NULL,
  predicted_value REAL NOT NULL,
  confidence_low REAL,
  confidence_high REAL,
  model_type TEXT DEFAULT 'linear', -- linear, moving_average, exponential
  generated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_forecast_tenant ON usage_forecasts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON usage_forecasts(forecast_date);
