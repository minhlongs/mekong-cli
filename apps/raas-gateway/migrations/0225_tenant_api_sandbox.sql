-- Migration 0225: Tenant API Sandbox
-- Isolated sandbox environments for tenants to test APIs

CREATE TABLE IF NOT EXISTS api_sandbox_environments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  sandbox_name TEXT NOT NULL,
  base_url TEXT,
  config_json TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_sandbox_environments_tenant ON api_sandbox_environments(tenant_id);

CREATE TABLE IF NOT EXISTS api_sandbox_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  sandbox_id TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_body TEXT,
  response_status INTEGER,
  response_body TEXT,
  latency_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_sandbox_requests_tenant ON api_sandbox_requests(tenant_id);
