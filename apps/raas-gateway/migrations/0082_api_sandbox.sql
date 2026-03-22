-- Migration 0082: API Sandbox — isolated test environments per tenant
CREATE TABLE IF NOT EXISTS sandbox_environments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT DEFAULT 'default',
  is_active INTEGER DEFAULT 1,
  config TEXT DEFAULT '{}',
  mock_responses TEXT DEFAULT '{}',
  request_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sandbox_requests (
  id TEXT PRIMARY KEY,
  sandbox_id TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_body TEXT,
  response_body TEXT,
  status_code INTEGER,
  latency_ms INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sandbox_tenant ON sandbox_environments(tenant_id);
CREATE INDEX idx_sandbox_requests ON sandbox_requests(sandbox_id, created_at);
