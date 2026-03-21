-- Migration 0050: Webhook v2 tables — exponential backoff delivery + delivery reports

CREATE TABLE IF NOT EXISTS webhook_endpoints_v2 (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  url TEXT NOT NULL,
  secret TEXT NOT NULL,
  events TEXT NOT NULL DEFAULT '["*"]',
  max_retries INTEGER DEFAULT 5,
  timeout_ms INTEGER DEFAULT 10000,
  active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_webhook_v2_tenant ON webhook_endpoints_v2(tenant_id, active);

CREATE TABLE IF NOT EXISTS webhook_deliveries_v2 (
  id TEXT PRIMARY KEY,
  webhook_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  status_code INTEGER,
  response_body TEXT,
  attempt_number INTEGER DEFAULT 1,
  next_retry_at TEXT,
  delivered INTEGER DEFAULT 0,
  latency_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_webhook_del_v2_webhook ON webhook_deliveries_v2(webhook_id, created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_del_v2_retry ON webhook_deliveries_v2(delivered, next_retry_at);
CREATE INDEX IF NOT EXISTS idx_webhook_del_v2_tenant ON webhook_deliveries_v2(tenant_id);
