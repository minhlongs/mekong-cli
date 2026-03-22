-- Admin Platform Alert Rules — metric-based alerting with incident tracking

CREATE TABLE IF NOT EXISTS platform_alert_rules (
  id TEXT PRIMARY KEY,
  rule_name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  condition TEXT NOT NULL,
  threshold REAL,
  severity TEXT DEFAULT 'warning',
  notification_channels TEXT DEFAULT '[]',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platform_alert_incidents (
  id TEXT PRIMARY KEY,
  rule_id TEXT NOT NULL,
  triggered_value REAL,
  status TEXT DEFAULT 'open',
  acknowledged_by TEXT,
  resolved_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric_name ON platform_alert_rules (metric_name);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON platform_alert_rules (severity);
CREATE INDEX IF NOT EXISTS idx_alert_incidents_rule_id ON platform_alert_incidents (rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_incidents_status ON platform_alert_incidents (status);
