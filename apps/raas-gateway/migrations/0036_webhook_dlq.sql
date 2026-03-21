-- Migration 0036: Webhook Dead Letter Queue
-- Stores deliveries that exhausted all retry attempts
CREATE TABLE IF NOT EXISTS webhook_dead_letters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  delivery_id TEXT NOT NULL,
  webhook_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  last_error TEXT,
  last_status_code INTEGER,
  total_attempts INTEGER NOT NULL DEFAULT 0,
  moved_at TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at TEXT,
  resolution TEXT,
  FOREIGN KEY (delivery_id) REFERENCES webhook_delivery_logs(id),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_dlq_tenant ON webhook_dead_letters(tenant_id, moved_at);
CREATE INDEX IF NOT EXISTS idx_dlq_unresolved ON webhook_dead_letters(resolved_at) WHERE resolved_at IS NULL;
