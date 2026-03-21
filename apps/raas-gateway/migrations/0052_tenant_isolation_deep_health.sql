-- Wave 24.2: Tenant Isolation violations audit + Deep Health snapshots

CREATE TABLE IF NOT EXISTS isolation_violations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  attempted_tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  action TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_isolation_violations_tenant ON isolation_violations(tenant_id, created_at);

CREATE TABLE IF NOT EXISTS health_snapshots (
  id TEXT PRIMARY KEY,
  overall_status TEXT NOT NULL,
  checks TEXT NOT NULL,
  timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_health_snapshots_time ON health_snapshots(timestamp);

CREATE TABLE IF NOT EXISTS health_checks (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
