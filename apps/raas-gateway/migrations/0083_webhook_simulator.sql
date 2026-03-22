-- Migration 0083: Webhook Simulator
-- Stores simulation runs and test endpoints for webhook delivery testing

CREATE TABLE IF NOT EXISTS webhook_simulations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  target_url TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL DEFAULT '{}',
  status TEXT DEFAULT 'pending',
  response_code INTEGER,
  response_body TEXT,
  latency_ms INTEGER,
  retry_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS webhook_test_endpoints (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_path TEXT NOT NULL,
  received_count INTEGER DEFAULT 0,
  last_payload TEXT,
  last_received_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_webhook_sim_tenant ON webhook_simulations(tenant_id, created_at);
CREATE INDEX idx_webhook_test_ep ON webhook_test_endpoints(tenant_id);
