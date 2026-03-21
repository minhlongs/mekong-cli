-- Tenant suspension system: tracks suspended accounts + payment retry queue
-- Used by tenant-suspension-service.ts for grace period and auto-resume logic

CREATE TABLE IF NOT EXISTS tenant_suspensions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  reason TEXT NOT NULL,
  suspended_at TEXT DEFAULT (datetime('now')),
  grace_period_ends TEXT,
  auto_resume_on_payment INTEGER DEFAULT 1,
  suspended_by TEXT DEFAULT 'system',
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE INDEX IF NOT EXISTS idx_suspension_tenant ON tenant_suspensions(tenant_id);

CREATE TABLE IF NOT EXISTS payment_retries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  attempt_number INTEGER DEFAULT 1,
  status TEXT DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  next_retry_at TEXT,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE INDEX IF NOT EXISTS idx_retry_tenant ON payment_retries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_retry_status ON payment_retries(status);
