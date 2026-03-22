-- Migration: Admin platform migration tracking tables
-- Tracks schema migrations applied to D1, with rollback history

CREATE TABLE IF NOT EXISTS platform_migrations (
  id TEXT PRIMARY KEY,
  migration_name TEXT NOT NULL,
  version TEXT NOT NULL,
  migration_type TEXT NOT NULL DEFAULT 'schema',
  status TEXT NOT NULL DEFAULT 'pending',
  sql_content TEXT,
  applied_by TEXT,
  applied_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS migration_rollback_history (
  id TEXT PRIMARY KEY,
  migration_id TEXT NOT NULL,
  rollback_reason TEXT,
  rolled_back_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_platform_migrations_version
  ON platform_migrations (version);

CREATE INDEX IF NOT EXISTS idx_platform_migrations_status
  ON platform_migrations (status);

CREATE INDEX IF NOT EXISTS idx_migration_rollback_history_migration_id
  ON migration_rollback_history (migration_id);
