-- Migration: Platform Service Mesh
-- Wave 51 — service registry, circuit breakers, traffic rules for RaaS Gateway

CREATE TABLE IF NOT EXISTS service_registry (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL UNIQUE,
  version TEXT DEFAULT '1.0.0',
  endpoint_url TEXT NOT NULL,
  health_check_url TEXT,
  status TEXT DEFAULT 'healthy',
  protocol TEXT DEFAULT 'http',
  metadata_json TEXT DEFAULT '{}',
  last_health_at TEXT,
  registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS circuit_breaker_configs (
  id TEXT PRIMARY KEY,
  service_id TEXT NOT NULL,
  failure_threshold INTEGER DEFAULT 5,
  recovery_timeout_ms INTEGER DEFAULT 30000,
  half_open_max_calls INTEGER DEFAULT 3,
  state TEXT DEFAULT 'closed',
  failure_count INTEGER DEFAULT 0,
  last_failure_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS traffic_rules (
  id TEXT PRIMARY KEY,
  source_service TEXT NOT NULL,
  target_service TEXT NOT NULL,
  weight INTEGER DEFAULT 100,
  rate_limit INTEGER DEFAULT 1000,
  timeout_ms INTEGER DEFAULT 5000,
  retry_count INTEGER DEFAULT 3,
  enabled INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_registry_name ON service_registry(service_name);
CREATE INDEX IF NOT EXISTS idx_service_registry_status ON service_registry(status);
CREATE INDEX IF NOT EXISTS idx_traffic_rules_source ON traffic_rules(source_service);
CREATE INDEX IF NOT EXISTS idx_traffic_rules_target ON traffic_rules(target_service);
