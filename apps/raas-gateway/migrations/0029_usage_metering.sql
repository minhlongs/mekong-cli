-- Usage metering tables for per-request tracking and quota enforcement

CREATE TABLE IF NOT EXISTS usage_records (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  method TEXT NOT NULL,
  status_code INTEGER,
  credits_consumed INTEGER DEFAULT 0,
  recorded_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_usage_tenant_date ON usage_records(tenant_id, recorded_at);

CREATE TABLE IF NOT EXISTS usage_quotas (
  tenant_id TEXT PRIMARY KEY,
  daily_limit INTEGER DEFAULT 1000,
  monthly_limit INTEGER DEFAULT 25000,
  overage_rate_cents INTEGER DEFAULT 1,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
