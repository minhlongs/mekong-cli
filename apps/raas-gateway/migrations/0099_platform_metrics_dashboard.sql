-- Migration: Platform Metrics Dashboard
-- Wave 40.3 — real-time KPIs, tenant growth, revenue tracking, system health aggregation

CREATE TABLE IF NOT EXISTS platform_metric_snapshots (
  id TEXT PRIMARY KEY,
  metric_name TEXT NOT NULL, -- total_tenants, active_tenants, mrr, arr, missions_today, api_calls_today
  metric_value REAL NOT NULL,
  dimension TEXT, -- optional grouping dimension
  snapshot_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_metric_snapshots_name ON platform_metric_snapshots(metric_name, snapshot_at);

CREATE TABLE IF NOT EXISTS platform_goals (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  target_value REAL NOT NULL,
  current_value REAL DEFAULT 0,
  deadline TEXT,
  status TEXT DEFAULT 'active', -- active, achieved, missed
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_goals_status ON platform_goals(status);
