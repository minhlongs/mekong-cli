-- Migration 0024: Dunning management tables

CREATE TABLE IF NOT EXISTS dunning_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  subscription_id TEXT,
  event_type TEXT NOT NULL,
  amount_cents INTEGER,
  currency TEXT DEFAULT 'usd',
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  next_retry_at TEXT,
  grace_period_end TEXT,
  status TEXT DEFAULT 'pending',
  resolved_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE TABLE IF NOT EXISTS win_back_emails (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  email_type TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now')),
  opened_at TEXT,
  clicked_at TEXT,
  converted_at TEXT,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_dunning_tenant ON dunning_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dunning_status ON dunning_events(status);
CREATE INDEX IF NOT EXISTS idx_winback_tenant ON win_back_emails(tenant_id);
