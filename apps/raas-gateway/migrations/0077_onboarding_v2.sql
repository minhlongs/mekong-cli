-- Onboarding V2: wizard flow with step tracking and analytics
CREATE TABLE IF NOT EXISTS onboarding_flows (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  current_step TEXT DEFAULT 'welcome',
  completed_steps TEXT DEFAULT '[]',
  skipped_steps TEXT DEFAULT '[]',
  metadata TEXT DEFAULT '{}',
  started_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  status TEXT DEFAULT 'in_progress'
);

CREATE TABLE IF NOT EXISTS onboarding_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  step TEXT NOT NULL,
  action TEXT NOT NULL,
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_onboarding_flows_tenant ON onboarding_flows(tenant_id);
CREATE INDEX idx_onboarding_events_tenant ON onboarding_events(tenant_id);
