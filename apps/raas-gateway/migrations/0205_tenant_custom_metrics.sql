-- Migration: Tenant custom metric definitions and data points
-- Allows tenants to define arbitrary metrics and record time-series data points

CREATE TABLE IF NOT EXISTS custom_metric_definitions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  unit TEXT NOT NULL DEFAULT 'count',
  aggregation_type TEXT NOT NULL DEFAULT 'sum',
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS custom_metric_data_points (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  metric_id TEXT NOT NULL,
  value REAL NOT NULL,
  dimensions_json TEXT NOT NULL DEFAULT '{}',
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_custom_metric_definitions_tenant_id
  ON custom_metric_definitions (tenant_id);

CREATE INDEX IF NOT EXISTS idx_custom_metric_data_points_tenant_id
  ON custom_metric_data_points (tenant_id);

CREATE INDEX IF NOT EXISTS idx_custom_metric_data_points_metric_id
  ON custom_metric_data_points (metric_id);
