-- Migration: Tenant API Schema Validation
-- Stores per-tenant JSON schema definitions for request/response validation
-- and records violations for observability.

CREATE TABLE IF NOT EXISTS api_schema_definitions (
  id               TEXT    PRIMARY KEY,
  tenant_id        TEXT    NOT NULL,
  schema_name      TEXT    NOT NULL,
  endpoint_pattern TEXT    NOT NULL,
  request_schema   TEXT,
  response_schema  TEXT,
  enabled          INTEGER NOT NULL DEFAULT 1,
  created_at       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_schema_definitions_tenant ON api_schema_definitions(tenant_id);

CREATE TABLE IF NOT EXISTS api_schema_violations (
  id             TEXT PRIMARY KEY,
  tenant_id      TEXT NOT NULL,
  schema_id      TEXT NOT NULL,
  violation_type TEXT NOT NULL,
  endpoint       TEXT,
  details        TEXT,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_schema_violations_tenant ON api_schema_violations(tenant_id);
