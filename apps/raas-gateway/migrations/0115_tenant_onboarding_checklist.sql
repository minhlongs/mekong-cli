-- Migration 0115: Tenant Onboarding Checklist
-- Tables: onboarding_checklists, onboarding_steps, onboarding_milestones

CREATE TABLE IF NOT EXISTS onboarding_checklists (
  id TEXT PRIMARY KEY DEFAULT ('oc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL UNIQUE,
  checklist_version TEXT NOT NULL DEFAULT 'v1',
  overall_progress INTEGER NOT NULL DEFAULT 0, -- 0-100
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at TEXT,
  current_step TEXT
);
CREATE INDEX IF NOT EXISTS idx_onb_checklist_tenant ON onboarding_checklists(tenant_id);

CREATE TABLE IF NOT EXISTS onboarding_steps (
  id TEXT PRIMARY KEY DEFAULT ('os_' || lower(hex(randomblob(8)))),
  checklist_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  step_key TEXT NOT NULL, -- 'create_api_key', 'submit_mission', 'setup_webhook', etc
  step_name TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  is_completed INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT,
  reward_credits INTEGER DEFAULT 0,
  reward_claimed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_onb_steps_checklist ON onboarding_steps(checklist_id);
CREATE INDEX IF NOT EXISTS idx_onb_steps_tenant ON onboarding_steps(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_onb_steps_unique ON onboarding_steps(tenant_id, step_key);

CREATE TABLE IF NOT EXISTS onboarding_milestones (
  id TEXT PRIMARY KEY DEFAULT ('om_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  milestone_key TEXT NOT NULL, -- 'first_mission', 'team_setup', 'production_ready'
  milestone_name TEXT NOT NULL,
  reward_type TEXT NOT NULL DEFAULT 'credits', -- credits, feature_unlock, badge
  reward_value TEXT NOT NULL DEFAULT '0',
  is_achieved INTEGER NOT NULL DEFAULT 0,
  achieved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_onb_milestones_tenant ON onboarding_milestones(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_onb_milestones_unique ON onboarding_milestones(tenant_id, milestone_key);
