-- Mission Analytics Dashboard: snapshots + configurable widgets
CREATE TABLE IF NOT EXISTS mission_analytics_snapshots (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  total_missions INTEGER DEFAULT 0,
  completed_missions INTEGER DEFAULT 0,
  failed_missions INTEGER DEFAULT 0,
  avg_duration_ms REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_analytics_snapshots_tenant ON mission_analytics_snapshots(tenant_id);

CREATE TABLE IF NOT EXISTS mission_analytics_widgets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  widget_name TEXT NOT NULL,
  widget_type TEXT NOT NULL DEFAULT 'chart',
  config_json TEXT,
  position INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_analytics_widgets_tenant ON mission_analytics_widgets(tenant_id);
