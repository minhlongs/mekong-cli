-- Migration: Admin tenant migration tracking
-- Tracks tenant tier/plan migrations with step-by-step audit trail

CREATE TABLE IF NOT EXISTS tenant_migrations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  from_tier TEXT NOT NULL,
  to_tier TEXT NOT NULL,
  migration_type TEXT NOT NULL DEFAULT 'upgrade',
  status TEXT NOT NULL DEFAULT 'pending',
  initiated_by TEXT,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_migrations_tenant ON tenant_migrations(tenant_id);

CREATE TABLE IF NOT EXISTS tenant_migration_steps (
  id TEXT PRIMARY KEY,
  migration_id TEXT NOT NULL,
  step_name TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  details TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_migration_steps_migration ON tenant_migration_steps(migration_id);
