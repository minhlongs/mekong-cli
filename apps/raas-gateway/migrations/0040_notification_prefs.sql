CREATE TABLE IF NOT EXISTS notification_preferences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL UNIQUE,
  email_enabled INTEGER NOT NULL DEFAULT 1,
  email_digest TEXT NOT NULL DEFAULT 'daily',
  webhook_failures INTEGER NOT NULL DEFAULT 1,
  mission_complete INTEGER NOT NULL DEFAULT 1,
  billing_alerts INTEGER NOT NULL DEFAULT 1,
  security_alerts INTEGER NOT NULL DEFAULT 1,
  marketing INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
