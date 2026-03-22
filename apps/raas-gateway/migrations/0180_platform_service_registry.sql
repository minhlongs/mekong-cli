-- Migration: Platform Service Registry
CREATE TABLE IF NOT EXISTS platform_services (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL,
  service_type TEXT NOT NULL,
  endpoint_url TEXT NOT NULL,
  health_check_url TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  version TEXT DEFAULT '1.0.0',
  metadata_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_platform_services_name ON platform_services(service_name);
CREATE INDEX IF NOT EXISTS idx_platform_services_status ON platform_services(status);

CREATE TABLE IF NOT EXISTS service_health_checks (
  id TEXT PRIMARY KEY,
  service_id TEXT NOT NULL,
  status TEXT NOT NULL,
  response_time_ms INTEGER,
  error_message TEXT,
  checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_service_health_checks_service ON service_health_checks(service_id);
