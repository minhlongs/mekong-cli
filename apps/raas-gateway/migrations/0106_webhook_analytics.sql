-- Wave 43: Tenant Webhooks Analytics
-- Tracks per-day delivery stats and per-endpoint health for each tenant

CREATE TABLE IF NOT EXISTS webhook_delivery_stats (
  id TEXT PRIMARY KEY DEFAULT ('wds_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  date TEXT NOT NULL,
  total_deliveries INTEGER NOT NULL DEFAULT 0,
  successful INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  retried INTEGER NOT NULL DEFAULT 0,
  avg_latency_ms REAL DEFAULT 0,
  p95_latency_ms REAL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_wds_tenant_date ON webhook_delivery_stats(tenant_id, date);

CREATE TABLE IF NOT EXISTS webhook_endpoint_health (
  id TEXT PRIMARY KEY DEFAULT ('weh_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  endpoint_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'healthy', -- healthy, degraded, down
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  last_success_at TEXT,
  last_failure_at TEXT,
  last_error TEXT,
  total_deliveries INTEGER NOT NULL DEFAULT 0,
  success_rate REAL DEFAULT 100.0,
  avg_response_ms REAL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_weh_tenant ON webhook_endpoint_health(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_weh_endpoint ON webhook_endpoint_health(tenant_id, endpoint_url);
