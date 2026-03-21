-- Migration 0037: Conversion funnel events table
-- Tracks user journey from page_view to subscription_active

CREATE TABLE IF NOT EXISTS conversion_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT,
  event_type TEXT NOT NULL,
  event_data TEXT NOT NULL DEFAULT '{}',
  session_id TEXT,
  source TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_conv_type_date ON conversion_events(event_type, created_at);
CREATE INDEX idx_conv_tenant ON conversion_events(tenant_id);
CREATE INDEX idx_conv_session ON conversion_events(session_id);
