-- Migration: Tenant API Mock Server
-- Stores configurable mock endpoints and their request logs per tenant

CREATE TABLE IF NOT EXISTS api_mock_endpoints (
  id              TEXT    PRIMARY KEY,
  tenant_id       TEXT    NOT NULL,
  mock_name       TEXT    NOT NULL,
  method          TEXT    NOT NULL DEFAULT 'GET',
  path_pattern    TEXT    NOT NULL,
  response_status INTEGER NOT NULL DEFAULT 200,
  response_body   TEXT,
  response_headers TEXT,
  delay_ms        INTEGER DEFAULT 0,
  enabled         INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_mock_endpoints_tenant ON api_mock_endpoints(tenant_id);

CREATE TABLE IF NOT EXISTS api_mock_requests (
  id             TEXT    PRIMARY KEY,
  tenant_id      TEXT    NOT NULL,
  mock_id        TEXT    NOT NULL,
  request_method TEXT,
  request_path   TEXT,
  matched        INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_mock_requests_tenant ON api_mock_requests(tenant_id);
