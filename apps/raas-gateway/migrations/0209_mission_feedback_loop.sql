-- Migration 0209: Mission Feedback Loop
-- Tables for collecting mission quality feedback and tracking resolution actions

CREATE TABLE IF NOT EXISTS mission_feedback (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  rating INTEGER NOT NULL,
  feedback_text TEXT,
  feedback_type TEXT NOT NULL DEFAULT 'quality',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_feedback_tenant_id ON mission_feedback (tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_feedback_mission_id ON mission_feedback (mission_id);

CREATE TABLE IF NOT EXISTS mission_feedback_actions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  feedback_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  action_details TEXT,
  resolved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_feedback_actions_tenant_id ON mission_feedback_actions (tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_feedback_actions_feedback_id ON mission_feedback_actions (feedback_id);
