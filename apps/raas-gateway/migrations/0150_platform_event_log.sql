-- Wave 57: Platform Event Log for RaaS Gateway
-- Tables: platform_events, event_categories, event_retention_configs

CREATE TABLE IF NOT EXISTS platform_events (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  category TEXT DEFAULT 'system',
  source TEXT DEFAULT 'gateway',
  actor_id TEXT,
  tenant_id TEXT,
  payload_json TEXT DEFAULT '{}',
  severity TEXT DEFAULT 'info',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_categories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  color TEXT DEFAULT '#6B7280',
  icon TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_retention_configs (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL UNIQUE,
  retention_days INTEGER DEFAULT 30,
  archive_enabled INTEGER DEFAULT 0,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for platform_events
CREATE INDEX IF NOT EXISTS idx_platform_events_event_type ON platform_events(event_type);
CREATE INDEX IF NOT EXISTS idx_platform_events_category ON platform_events(category);
CREATE INDEX IF NOT EXISTS idx_platform_events_tenant_id ON platform_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platform_events_severity ON platform_events(severity);
CREATE INDEX IF NOT EXISTS idx_platform_events_created_at ON platform_events(created_at);

-- Seed default event categories
INSERT OR IGNORE INTO event_categories (id, name, description, color, icon) VALUES
  ('cat_system',      'system',      'Core gateway and platform events',         '#6B7280', 'server'),
  ('cat_security',    'security',    'Auth, access control, and threat events',  '#EF4444', 'shield'),
  ('cat_billing',     'billing',     'Subscription, payment, and usage events',  '#F59E0B', 'credit-card'),
  ('cat_mission',     'mission',     'Mission lifecycle and execution events',    '#3B82F6', 'rocket'),
  ('cat_integration', 'integration', 'External service and webhook events',       '#10B981', 'plug');

-- Seed default retention configs
INSERT OR IGNORE INTO event_retention_configs (id, category, retention_days, archive_enabled) VALUES
  ('ret_system',      'system',      30,  0),
  ('ret_security',    'security',    90,  1),
  ('ret_billing',     'billing',     365, 1),
  ('ret_mission',     'mission',     60,  0),
  ('ret_integration', 'integration', 30,  0);
