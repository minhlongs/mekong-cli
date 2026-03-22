-- Migration 0093: Platform Notifications Hub
-- Centralized multi-channel notification dispatch: in-app, email, webhook, telegram, slack

CREATE TABLE IF NOT EXISTS notification_channels (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel_type TEXT NOT NULL, -- email, webhook, telegram, slack, in_app
  config TEXT NOT NULL, -- JSON: { url?, token?, email?, chat_id? }
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_notif_channels_tenant ON notification_channels(tenant_id);

CREATE TABLE IF NOT EXISTS notification_log (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel_id TEXT,
  channel_type TEXT NOT NULL,
  event_type TEXT NOT NULL, -- mission_completed, budget_alert, team_invite, etc
  subject TEXT,
  body TEXT,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, sent, failed
  error TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  sent_at TEXT
);
CREATE INDEX idx_notif_log_tenant ON notification_log(tenant_id, created_at);
CREATE INDEX idx_notif_log_status ON notification_log(status);

CREATE TABLE IF NOT EXISTS notification_templates (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL UNIQUE,
  subject_template TEXT NOT NULL,
  body_template TEXT NOT NULL,
  channels TEXT NOT NULL DEFAULT '["in_app"]', -- JSON array of default channels
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
