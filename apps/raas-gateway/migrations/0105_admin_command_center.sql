-- Admin Command Center: audit log for executed commands + scheduled command registry
-- Wave 42 feature

CREATE TABLE IF NOT EXISTS admin_commands (
  id TEXT PRIMARY KEY DEFAULT ('cmd_' || lower(hex(randomblob(8)))),
  command_type TEXT NOT NULL, -- system_check, cache_clear, tenant_action, broadcast, maintenance
  command_name TEXT NOT NULL,
  parameters TEXT DEFAULT '{}', -- JSON
  executed_by TEXT NOT NULL, -- admin identifier
  status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
  result TEXT, -- JSON result
  error TEXT,
  target_tenant_id TEXT, -- optional tenant scope
  started_at TEXT,
  completed_at TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cmd_type ON admin_commands(command_type);
CREATE INDEX IF NOT EXISTS idx_cmd_status ON admin_commands(status);
CREATE INDEX IF NOT EXISTS idx_cmd_created ON admin_commands(created_at);

CREATE TABLE IF NOT EXISTS scheduled_commands (
  id TEXT PRIMARY KEY DEFAULT ('scmd_' || lower(hex(randomblob(8)))),
  command_type TEXT NOT NULL,
  command_name TEXT NOT NULL,
  parameters TEXT DEFAULT '{}',
  cron_expression TEXT, -- e.g. '0 */6 * * *'
  is_active INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  next_run_at TEXT,
  run_count INTEGER NOT NULL DEFAULT 0,
  failure_count INTEGER NOT NULL DEFAULT 0,
  max_failures INTEGER DEFAULT 3, -- auto-disable after N failures
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_scmd_active ON scheduled_commands(is_active, next_run_at);
CREATE INDEX IF NOT EXISTS idx_scmd_type ON scheduled_commands(command_type);
