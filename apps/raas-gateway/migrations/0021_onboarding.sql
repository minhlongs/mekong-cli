CREATE TABLE IF NOT EXISTS onboarding_progress (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  steps_completed TEXT DEFAULT '[]',
  current_step INTEGER DEFAULT 0,
  completed_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE INDEX idx_onboarding_tenant ON onboarding_progress(tenant_id);
