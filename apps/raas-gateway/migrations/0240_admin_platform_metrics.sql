-- Platform Metrics — time-series KPI storage and alert thresholds for admin dashboard
CREATE TABLE IF NOT EXISTS platform_metrics (
  id TEXT PRIMARY KEY,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  unit TEXT NOT NULL DEFAULT 'count',
  tags TEXT,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_metrics_name ON platform_metrics(metric_name);

-- Platform Metric Alerts — threshold rules that fire notifications when metrics breach
CREATE TABLE IF NOT EXISTS platform_metric_alerts (
  id TEXT PRIMARY KEY,
  metric_name TEXT NOT NULL,
  threshold REAL NOT NULL,
  comparison TEXT NOT NULL DEFAULT 'gt',
  notification_channel TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_metric_alerts_name ON platform_metric_alerts(metric_name);
