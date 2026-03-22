-- Migration 0084: API Usage Analytics — per-endpoint stats with latency percentiles and error breakdown

CREATE TABLE IF NOT EXISTS api_endpoint_stats (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL,
  period TEXT NOT NULL,
  total_requests INTEGER DEFAULT 0,
  success_count INTEGER DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  avg_latency_ms REAL DEFAULT 0,
  p50_latency_ms REAL DEFAULT 0,
  p95_latency_ms REAL DEFAULT 0,
  p99_latency_ms REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id, endpoint, method, period)
);

CREATE TABLE IF NOT EXISTS api_error_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  error_message TEXT,
  count INTEGER DEFAULT 1,
  first_seen_at TEXT DEFAULT (datetime('now')),
  last_seen_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_endpoint_stats ON api_endpoint_stats(tenant_id, period);
CREATE INDEX IF NOT EXISTS idx_error_logs ON api_error_logs(tenant_id, endpoint);
