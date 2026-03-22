-- Migration: Tenant API Circuit Breaker
-- Tables: api_circuit_breakers, api_circuit_breaker_events

CREATE TABLE IF NOT EXISTS api_circuit_breakers (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  failure_threshold INTEGER NOT NULL DEFAULT 5,
  recovery_timeout_ms INTEGER NOT NULL DEFAULT 30000,
  status TEXT NOT NULL DEFAULT 'closed',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_circuit_breakers_tenant ON api_circuit_breakers(tenant_id);

CREATE TABLE IF NOT EXISTS api_circuit_breaker_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  breaker_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  failure_count INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_circuit_breaker_events_tenant ON api_circuit_breaker_events(tenant_id);
