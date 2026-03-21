-- Migration: Create alerts table for credit usage warnings and upgrade nudges
CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('low_credits', 'credits_exhausted', 'daily_limit', 'upgrade_available')),
  message TEXT NOT NULL,
  read INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_tenant_unread ON alerts(tenant_id, read);
