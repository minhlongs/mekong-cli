-- Admin Platform Backup: backup records and schedules
CREATE TABLE IF NOT EXISTS platform_backups (
  id TEXT PRIMARY KEY,
  backup_name TEXT NOT NULL,
  backup_type TEXT NOT NULL DEFAULT 'full',
  size_bytes INTEGER,
  storage_path TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_backups_type ON platform_backups(backup_type);

CREATE TABLE IF NOT EXISTS platform_backup_schedules (
  id TEXT PRIMARY KEY,
  schedule_name TEXT NOT NULL,
  cron_expression TEXT NOT NULL,
  backup_type TEXT NOT NULL DEFAULT 'incremental',
  retention_days INTEGER NOT NULL DEFAULT 30,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_backup_schedules_enabled ON platform_backup_schedules(enabled);
