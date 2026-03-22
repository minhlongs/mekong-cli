CREATE TABLE IF NOT EXISTS platform_backups (
  id TEXT PRIMARY KEY, backup_type TEXT NOT NULL DEFAULT 'full',
  storage_location TEXT NOT NULL, size_bytes INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', initiated_by TEXT,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_platform_backups_status ON platform_backups(status);

CREATE TABLE IF NOT EXISTS platform_restore_points (
  id TEXT PRIMARY KEY, backup_id TEXT NOT NULL, restore_type TEXT NOT NULL DEFAULT 'full',
  status TEXT NOT NULL DEFAULT 'pending', initiated_by TEXT,
  target_environment TEXT DEFAULT 'staging',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_platform_restore_points_backup ON platform_restore_points(backup_id);
