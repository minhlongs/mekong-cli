-- Data Retention Policies: configurable per-tenant, per-data-type retention rules
CREATE TABLE IF NOT EXISTS retention_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  data_type TEXT NOT NULL,          -- missions, audit_logs, analytics, notifications, webhooks
  retention_days INTEGER NOT NULL DEFAULT 90,
  auto_purge INTEGER DEFAULT 0,     -- 1 = auto-delete on schedule
  archive_before_purge INTEGER DEFAULT 1, -- 1 = export before purging
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE UNIQUE INDEX idx_retention_tenant_type ON retention_policies(tenant_id, data_type);

-- Purge execution history per policy
CREATE TABLE IF NOT EXISTS retention_purge_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  data_type TEXT NOT NULL,
  records_purged INTEGER DEFAULT 0,
  records_archived INTEGER DEFAULT 0,
  purged_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (policy_id) REFERENCES retention_policies(id)
);
CREATE INDEX idx_purge_log_tenant ON retention_purge_logs(tenant_id);
