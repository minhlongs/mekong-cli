-- Migration 0085: Tenant Backup & Restore — point-in-time snapshots per tenant
CREATE TABLE IF NOT EXISTS tenant_backups (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  backup_type TEXT DEFAULT 'full',
  status TEXT DEFAULT 'pending',
  data TEXT,
  size_bytes INTEGER DEFAULT 0,
  tables_included TEXT DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  expires_at TEXT
);

CREATE TABLE IF NOT EXISTS backup_restore_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  backup_id TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  details TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT
);

CREATE INDEX idx_backups_tenant ON tenant_backups(tenant_id, created_at);
CREATE INDEX idx_restore_logs ON backup_restore_logs(tenant_id);
