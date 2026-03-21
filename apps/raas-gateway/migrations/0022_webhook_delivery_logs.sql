-- Migration 0022: Webhook delivery logs + dead letter queue
CREATE TABLE IF NOT EXISTS webhook_delivery_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  url TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  http_status INTEGER,
  response_body TEXT,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  next_retry_at TEXT,
  last_attempted_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE INDEX IF NOT EXISTS idx_wdl_tenant ON webhook_delivery_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wdl_status ON webhook_delivery_logs(status);
CREATE INDEX IF NOT EXISTS idx_wdl_retry ON webhook_delivery_logs(status, next_retry_at);
