-- Migration: mission_collaboration
-- Adds collaborator roster and threaded comments per mission

CREATE TABLE IF NOT EXISTS mission_collaborators (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  mission_id  TEXT NOT NULL,
  user_id     TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'viewer',
  invited_by  TEXT,
  joined_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_collaborators_tenant ON mission_collaborators(tenant_id);

CREATE TABLE IF NOT EXISTS mission_collaboration_comments (
  id         TEXT PRIMARY KEY,
  tenant_id  TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  user_id    TEXT NOT NULL,
  comment    TEXT NOT NULL,
  parent_id  TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_collaboration_comments_mission ON mission_collaboration_comments(mission_id);
