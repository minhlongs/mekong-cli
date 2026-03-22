-- Admin Platform Health Dashboard: health checks + incidents tracking
CREATE TABLE IF NOT EXISTS platform_health_checks (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL,
  check_type TEXT NOT NULL DEFAULT 'http',
  status TEXT NOT NULL DEFAULT 'healthy',
  response_time_ms INTEGER,
  last_checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_health_checks_service ON platform_health_checks(service_name);

CREATE TABLE IF NOT EXISTS platform_health_incidents (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL,
  incident_type TEXT NOT NULL,
  description TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_health_incidents_service ON platform_health_incidents(service_name);
