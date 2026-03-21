-- Migration 0059: Notification Center
-- Tables: notification_templates, notifications, notification_preferences

-- Notification templates for reusable message patterns
CREATE TABLE IF NOT EXISTS notification_templates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  channel TEXT NOT NULL CHECK(channel IN ('in_app', 'email', 'push', 'webhook')),
  subject TEXT,
  body_template TEXT NOT NULL,
  variables TEXT DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_notif_templates_tenant ON notification_templates(tenant_id);

-- Notifications sent to recipients
CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  template_id TEXT,
  channel TEXT NOT NULL,
  recipient TEXT NOT NULL,
  subject TEXT,
  body TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'delivered', 'failed', 'read')),
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now')),
  read_at TEXT
);
CREATE INDEX idx_notif_tenant ON notifications(tenant_id);
CREATE INDEX idx_notif_status ON notifications(tenant_id, status);
CREATE INDEX idx_notif_recipient ON notifications(recipient);

-- Per-channel notification preferences per tenant
CREATE TABLE IF NOT EXISTS notification_preferences (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel TEXT NOT NULL,
  enabled INTEGER DEFAULT 1,
  quiet_hours_start TEXT,
  quiet_hours_end TEXT,
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id, channel)
);
