-- Onboarding Flow Schema
-- Supports: signup flow, tutorial tracking, usage milestones, feedback collection

-- Onboarding states table
CREATE TABLE IF NOT EXISTS onboarding_states (
  tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  email_verified INTEGER DEFAULT 0,
  verification_code TEXT,
  verification_code_expires TEXT,
  welcome_email_sent INTEGER DEFAULT 0,
  onboarding_step INTEGER DEFAULT 0,
  onboarding_completed INTEGER DEFAULT 0,
  first_command_run INTEGER DEFAULT 0,
  tutorial_step INTEGER DEFAULT 1,
  tutorial_completed INTEGER DEFAULT 0,
  feedback_submitted INTEGER DEFAULT 0,
  nps_score INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_onboarding_states_email ON onboarding_states(email);
CREATE INDEX IF NOT EXISTS idx_onboarding_states_verification_code ON onboarding_states(verification_code);

-- Usage milestones tracking
CREATE TABLE IF NOT EXISTS usage_milestones (
  tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  tier_name TEXT NOT NULL DEFAULT 'free',
  tier_limit INTEGER NOT NULL DEFAULT 200,
  current_usage INTEGER NOT NULL DEFAULT 0,
  milestone_reached INTEGER,
  milestone_10_sent INTEGER DEFAULT 0,
  milestone_50_sent INTEGER DEFAULT 0,
  milestone_80_sent INTEGER DEFAULT 0,
  milestone_100_sent INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_milestones_tier ON usage_milestones(tier_name);
CREATE INDEX IF NOT EXISTS idx_usage_milestones_usage ON usage_milestones(current_usage);

-- Feedback entries table
CREATE TABLE IF NOT EXISTS feedback_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('nps', 'feature', 'general')),
  score INTEGER,
  feedback TEXT NOT NULL DEFAULT '',
  category TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_feedback_entries_tenant ON feedback_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_feedback_entries_type ON feedback_entries(type);
CREATE INDEX IF NOT EXISTS idx_feedback_entries_created ON feedback_entries(created_at);
