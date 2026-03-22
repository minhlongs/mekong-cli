-- Wave 56: Admin System Health for RaaS Gateway
-- Tables: system_metrics, component_health, uptime_records, alert_rules

CREATE TABLE IF NOT EXISTS system_metrics (
  id TEXT PRIMARY KEY,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  unit TEXT DEFAULT 'count',
  component TEXT DEFAULT 'gateway',
  tags_json TEXT DEFAULT '{}',
  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS component_health (
  id TEXT PRIMARY KEY,
  component_name TEXT NOT NULL UNIQUE,
  status TEXT DEFAULT 'healthy',
  last_check_at TEXT,
  response_time_ms INTEGER,
  error_message TEXT,
  metadata_json TEXT DEFAULT '{}',
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS uptime_records (
  id TEXT PRIMARY KEY,
  component_name TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  duration_seconds INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alert_rules (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  condition TEXT NOT NULL,
  threshold REAL NOT NULL,
  severity TEXT DEFAULT 'warning',
  enabled INTEGER DEFAULT 1,
  last_triggered_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for system_metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);

-- Indexes for component_health
CREATE INDEX IF NOT EXISTS idx_component_health_name ON component_health(component_name);
CREATE INDEX IF NOT EXISTS idx_component_health_status ON component_health(status);

-- Indexes for uptime_records
CREATE INDEX IF NOT EXISTS idx_uptime_records_component ON uptime_records(component_name);
CREATE INDEX IF NOT EXISTS idx_uptime_records_status ON uptime_records(status);

-- Indexes for alert_rules
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric ON alert_rules(metric_name);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
