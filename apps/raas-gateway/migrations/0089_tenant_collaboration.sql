-- Wave 37.2: Tenant Collaboration — comments, shared views, activity feed

CREATE TABLE IF NOT EXISTS mission_comments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  content TEXT NOT NULL,
  parent_id TEXT, -- for threaded replies
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_comments_mission ON mission_comments(mission_id);
CREATE INDEX idx_comments_tenant ON mission_comments(tenant_id);

CREATE TABLE IF NOT EXISTS shared_views (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  view_type TEXT NOT NULL DEFAULT 'mission_list', -- mission_list, dashboard, analytics
  filters TEXT, -- JSON filters
  shared_with TEXT, -- JSON array of user_ids, or 'all'
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_shared_views_tenant ON shared_views(tenant_id);

CREATE TABLE IF NOT EXISTS activity_feed (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL, -- comment_added, mission_created, view_shared, member_joined
  resource_type TEXT NOT NULL, -- mission, view, team
  resource_id TEXT,
  metadata TEXT, -- JSON
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_activity_tenant_time ON activity_feed(tenant_id, created_at);
