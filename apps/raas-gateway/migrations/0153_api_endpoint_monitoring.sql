-- Wave 58: API Endpoint Monitoring for RaaS Gateway
-- Tables: endpoint_metrics, endpoint_availability, endpoint_alerts

CREATE TABLE IF NOT EXISTS endpoint_metrics (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  method TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  tenant_id TEXT,
  error_message TEXT,
  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS endpoint_availability (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  method TEXT DEFAULT 'GET',
  status TEXT DEFAULT 'up',
  last_check_at TEXT,
  uptime_pct REAL DEFAULT 100,
  avg_response_ms INTEGER DEFAULT 0,
  check_count INTEGER DEFAULT 0,
  fail_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS endpoint_alerts (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  condition_json TEXT DEFAULT '{}',
  threshold REAL NOT NULL,
  severity TEXT DEFAULT 'warning',
  enabled INTEGER DEFAULT 1,
  last_triggered_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for endpoint_metrics
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_path ON endpoint_metrics(path);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_method ON endpoint_metrics(method);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_status_code ON endpoint_metrics(status_code);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_tenant_id ON endpoint_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_recorded_at ON endpoint_metrics(recorded_at);

-- Indexes for endpoint_availability
CREATE UNIQUE INDEX IF NOT EXISTS idx_endpoint_availability_path_method ON endpoint_availability(path, method);

-- Indexes for endpoint_alerts
CREATE INDEX IF NOT EXISTS idx_endpoint_alerts_path ON endpoint_alerts(path);
CREATE INDEX IF NOT EXISTS idx_endpoint_alerts_alert_type ON endpoint_alerts(alert_type);
