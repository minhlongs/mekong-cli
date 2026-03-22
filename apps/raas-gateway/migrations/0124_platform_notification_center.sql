-- Migration 0124: Platform Notification Center
-- Unified in-app, email, and multi-channel notification management for tenants

CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  notification_type TEXT DEFAULT 'info', -- info, warning, error, success
  channel TEXT DEFAULT 'in_app',         -- in_app, email, sms, push
  status TEXT DEFAULT 'pending',         -- pending, delivered, failed, read
  read_at TEXT,
  delivered_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);

CREATE TABLE IF NOT EXISTS notification_preferences (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel TEXT NOT NULL,               -- in_app, email, sms, push
  enabled INTEGER DEFAULT 1,
  config_json TEXT DEFAULT '{}',       -- channel-specific config
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notif_prefs_tenant_id ON notification_preferences(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_notif_prefs_tenant_channel ON notification_preferences(tenant_id, channel);

CREATE TABLE IF NOT EXISTS notification_templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  subject TEXT NOT NULL,
  body_template TEXT NOT NULL,
  template_type TEXT DEFAULT 'email',  -- email, sms, push, in_app
  variables_json TEXT DEFAULT '[]',    -- JSON array of variable names
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notif_templates_type ON notification_templates(template_type);
